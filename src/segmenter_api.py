import pickle
import spacy
from rst_edu_reader import RSTData
from atten_seg import AttnSegModel
from config import parse_args
from flask import Flask
from flask import request, jsonify
import pandas as pd

args = parse_args()
args.segment = True
args.gpu = None
args.batch_size = 64

spacy_nlp = spacy.load('en', disable=['parser', 'ner', 'textcat'])

rst_data = RSTData()
with open(args.word_vocab_path, 'rb') as fin:
    word_vocab = pickle.load(fin)

rst_data.word_vocab = word_vocab

model = AttnSegModel(args, word_vocab)
model.restore('best', args.model_dir)

if model.use_ema:
    model.sess.run(model.ema_backup_op)
    model.sess.run(model.ema_assign_op)


def segment_text(args, raw_sents):
    """
    Segment raw text into edus.
    """

    samples = []
    for sent in spacy_nlp.pipe(raw_sents, batch_size=1000, n_threads=5):
        samples.append({'words': [token.text for token in sent],
                        'edu_seg_indices': []})
    rst_data.test_samples = samples
    data_batches = rst_data.gen_mini_batches(args.batch_size, test=True, shuffle=False)

    edus = []
    for batch in data_batches:
        batch_pred_segs = model.segment(batch)
        for sample, pred_segs in zip(batch['raw_data'], batch_pred_segs):
            edus.append([])
            one_edu_words = []
            for word_idx, word in enumerate(sample['words']):
                if word_idx in pred_segs:
                    edus[-1].append(' '.join(one_edu_words))
                    one_edu_words = []
                one_edu_words.append(word)
            if one_edu_words:
                edus[-1].append(' '.join(one_edu_words))
    return edus


app = Flask(__name__)


@app.route('/edu', methods=['POST'])
def edu():
    text = request.json["text"]
    df = pd.DataFrame(text, columns=["phrase"])
    df["_len"] = df.phrase.str.split().map(len)
    t = df[df._len > 4]
    seg = segment_text(args, t.phrase.tolist())
    seg = list(map(lambda x: " | ".join(x), seg))
    seg = pd.DataFrame(index=t.index, data=seg, columns=["seg"])
    df = pd.concat([df, seg], axis=1)
    df.seg = df.apply(lambda x: x.seg if not pd.isna(x.seg) else x.phrase, axis=1)

    return jsonify(df.seg.to_list())


if __name__ == '__main__':
    app.run()

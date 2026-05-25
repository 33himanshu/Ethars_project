"""
Benchmark Dataset
------------------
20 labeled query-answer pairs based on "Attention Is All You Need" (Vaswani et al., 2017).
Used for offline evaluation of retrieval accuracy and answer quality.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvalSample:
    query_id: str
    query: str
    expected_answer_keywords: list[str]   # Keywords that must appear in a correct answer
    relevant_chunk_topics: list[str]       # Topics that relevant chunks should cover
    difficulty: str                        # easy | medium | hard
    category: str                          # factual | conceptual | comparative


ATTENTION_PAPER_DATASET: list[EvalSample] = [
    EvalSample(
        query_id="q01",
        query="What attention mechanism is proposed in this paper and how does it differ from RNNs?",
        expected_answer_keywords=["self-attention", "multi-head", "sequential", "parallelization", "recurrent"],
        relevant_chunk_topics=["transformer architecture", "self-attention", "RNN comparison"],
        difficulty="medium",
        category="comparative",
    ),
    EvalSample(
        query_id="q02",
        query="What is the Transformer model architecture?",
        expected_answer_keywords=["encoder", "decoder", "attention", "feed-forward", "layers"],
        relevant_chunk_topics=["model architecture", "encoder-decoder"],
        difficulty="easy",
        category="factual",
    ),
    EvalSample(
        query_id="q03",
        query="How does multi-head attention work?",
        expected_answer_keywords=["heads", "queries", "keys", "values", "concatenate", "linear"],
        relevant_chunk_topics=["multi-head attention", "attention mechanism"],
        difficulty="medium",
        category="conceptual",
    ),
    EvalSample(
        query_id="q04",
        query="What is the scaled dot-product attention formula?",
        expected_answer_keywords=["softmax", "QK", "sqrt", "dk", "values"],
        relevant_chunk_topics=["scaled dot-product attention", "attention formula"],
        difficulty="hard",
        category="factual",
    ),
    EvalSample(
        query_id="q05",
        query="Why does the Transformer use positional encoding?",
        expected_answer_keywords=["position", "sequence order", "sine", "cosine", "no recurrence"],
        relevant_chunk_topics=["positional encoding", "sequence order"],
        difficulty="medium",
        category="conceptual",
    ),
    EvalSample(
        query_id="q06",
        query="What training data was used for the machine translation experiments?",
        expected_answer_keywords=["WMT", "English-German", "English-French", "BPE", "tokens"],
        relevant_chunk_topics=["training data", "WMT dataset", "machine translation"],
        difficulty="easy",
        category="factual",
    ),
    EvalSample(
        query_id="q07",
        query="What BLEU score did the Transformer achieve on English-German translation?",
        expected_answer_keywords=["28.4", "BLEU", "English-German", "WMT 2014"],
        relevant_chunk_topics=["BLEU score", "translation results", "English-German"],
        difficulty="easy",
        category="factual",
    ),
    EvalSample(
        query_id="q08",
        query="How does the Transformer handle long-range dependencies compared to CNNs?",
        expected_answer_keywords=["constant", "path length", "convolutional", "O(1)", "O(n)"],
        relevant_chunk_topics=["long-range dependencies", "CNN comparison", "path length"],
        difficulty="hard",
        category="comparative",
    ),
    EvalSample(
        query_id="q09",
        query="What optimizer and learning rate schedule was used?",
        expected_answer_keywords=["Adam", "warmup", "learning rate", "steps", "beta"],
        relevant_chunk_topics=["optimizer", "Adam", "learning rate schedule"],
        difficulty="medium",
        category="factual",
    ),
    EvalSample(
        query_id="q10",
        query="What regularization techniques were applied during training?",
        expected_answer_keywords=["dropout", "label smoothing", "residual"],
        relevant_chunk_topics=["regularization", "dropout", "label smoothing"],
        difficulty="medium",
        category="factual",
    ),
    EvalSample(
        query_id="q11",
        query="What is the role of the feed-forward network in each Transformer layer?",
        expected_answer_keywords=["feed-forward", "position-wise", "ReLU", "linear", "sublayer"],
        relevant_chunk_topics=["feed-forward network", "position-wise FFN"],
        difficulty="medium",
        category="conceptual",
    ),
    EvalSample(
        query_id="q12",
        query="How many attention heads and layers does the base Transformer model use?",
        expected_answer_keywords=["6", "8", "heads", "layers", "512", "d_model"],
        relevant_chunk_topics=["model hyperparameters", "base model", "attention heads"],
        difficulty="easy",
        category="factual",
    ),
    EvalSample(
        query_id="q13",
        query="What is the computational complexity of self-attention per layer?",
        expected_answer_keywords=["O(n²)", "sequence length", "complexity", "d"],
        relevant_chunk_topics=["computational complexity", "self-attention complexity"],
        difficulty="hard",
        category="factual",
    ),
    EvalSample(
        query_id="q14",
        query="How does the Transformer perform on English constituency parsing?",
        expected_answer_keywords=["parsing", "WSJ", "semi-supervised", "F1"],
        relevant_chunk_topics=["constituency parsing", "English parsing", "WSJ"],
        difficulty="medium",
        category="factual",
    ),
    EvalSample(
        query_id="q15",
        query="What is the purpose of residual connections in the Transformer?",
        expected_answer_keywords=["residual", "layer normalization", "gradient", "sublayer"],
        relevant_chunk_topics=["residual connections", "layer normalization"],
        difficulty="medium",
        category="conceptual",
    ),
    EvalSample(
        query_id="q16",
        query="How does the decoder differ from the encoder in the Transformer?",
        expected_answer_keywords=["masked", "encoder-decoder attention", "autoregressive", "cross-attention"],
        relevant_chunk_topics=["decoder", "masked attention", "encoder-decoder"],
        difficulty="medium",
        category="comparative",
    ),
    EvalSample(
        query_id="q17",
        query="What is byte-pair encoding and why is it used?",
        expected_answer_keywords=["BPE", "subword", "vocabulary", "tokenization"],
        relevant_chunk_topics=["BPE", "byte-pair encoding", "tokenization"],
        difficulty="medium",
        category="conceptual",
    ),
    EvalSample(
        query_id="q18",
        query="What hardware was used to train the Transformer models?",
        expected_answer_keywords=["GPU", "P100", "NVIDIA", "hours", "training time"],
        relevant_chunk_topics=["training hardware", "GPU", "training time"],
        difficulty="easy",
        category="factual",
    ),
    EvalSample(
        query_id="q19",
        query="How does attention masking work in the decoder?",
        expected_answer_keywords=["mask", "future positions", "autoregressive", "prevent"],
        relevant_chunk_topics=["masked self-attention", "decoder masking"],
        difficulty="hard",
        category="conceptual",
    ),
    EvalSample(
        query_id="q20",
        query="What are the key advantages of the Transformer over sequence-to-sequence models?",
        expected_answer_keywords=["parallelization", "training time", "state-of-the-art", "attention", "recurrence"],
        relevant_chunk_topics=["advantages", "seq2seq comparison", "parallelization"],
        difficulty="medium",
        category="comparative",
    ),
]


def load_dataset() -> list[EvalSample]:
    """Load the evaluation dataset."""
    return ATTENTION_PAPER_DATASET


def get_sample_by_id(query_id: str) -> Optional[EvalSample]:
    for sample in ATTENTION_PAPER_DATASET:
        if sample.query_id == query_id:
            return sample
    return None

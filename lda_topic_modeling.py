# -*- coding: utf-8 -*-
"""
@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2018

Resources used:
https://www.analyticsvidhya.com/blog/2016/08/beginners-guide-to-topic-modeling-in-python/
https://datascience.blog.wzb.eu/2016/06/17/creating-a-sparse-document-term-matrix-for-topic-modeling-via-lda/

Dependencies:
nltk
numpy
scipy
lda

Requirements:
nltk.download('wordnet')
nltk.download('stopwords')
"""

import string
import numpy as np
import lda
from nltk.corpus import stopwords 
from nltk.stem.wordnet import WordNetLemmatizer
from scipy.sparse import coo_matrix

#https://www.analyticsvidhya.com/blog/2016/08/beginners-guide-to-topic-modeling-in-python/
stop = set(stopwords.words('english')) # creates set for faster lookups
exclude = set(string.punctuation) 
lemma = WordNetLemmatizer()
def clean(doc):
    stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    return normalized


# Create sparse terms: https://datascience.blog.wzb.eu/2016/06/17/creating-a-sparse-document-term-matrix-for-topic-modeling-via-lda/
def GetNTopics(docs, num_topics, n_top_words):
    vocab = set()
    n_nonzero = 0
    for doc in docs:
        unique_terms = set(doc)    # all unique terms of this doc
        vocab |= unique_terms           # set union: add unique terms of this doc
        n_nonzero += len(unique_terms)  # add count of unique terms in this doc

    vocab_np = np.array(list(vocab))
    vocab_sorter = np.argsort(vocab_np)
    
    ndocs = len(docs)
    nvocab = len(vocab)
        
    #Note: dtype default normally float, should check size of issues and use int if < 2^31
    data = np.empty(n_nonzero, dtype=np.int64)     # all non-zero term frequencies at data[k]
    rows = np.empty(n_nonzero, dtype=np.int64)     # row index for kth data item (kth term freq.)
    cols = np.empty(n_nonzero, dtype=np.int64)     # column index for kth data item (kth term freq.)
    
    ind = 0     # current index in the sparse matrix data
    
    # go through all documents with their terms
    for doc_idx, doc_terms in enumerate(docs):
        # find indices into  such that, if the corresponding elements in  were
        # inserted before the indices, the order of  would be preserved
        # -> array of indices of  in 
        term_indices = vocab_sorter[np.searchsorted(vocab_np, doc_terms, sorter=vocab_sorter)]
    
        # count the unique terms of the document and get their vocabulary indices
        uniq_indices, counts = np.unique(term_indices, return_counts=True)
        n_vals = len(uniq_indices)  # = number of unique terms
        ind_end = ind + n_vals  #  to  is the slice that we will fill with data
    
        data[ind:ind_end] = counts                  # save the counts (term frequencies)
        cols[ind:ind_end] = uniq_indices            # save the column index: index in 
        rows[ind:ind_end] = np.repeat(doc_idx, n_vals)  # save it as repeated value
    
        ind = ind_end  # resume with next document -> add data to the end
    
    dtm = coo_matrix((data, (rows, cols)), shape=(ndocs, nvocab), dtype=np.int64)
    
    #collapsed gibbs sampling LDA
    model = lda.LDA(n_topics=num_topics, n_iter=2000, random_state=1)  #http://pythonhosted.org/lda/api.html#module-lda.lda 
    model.fit(dtm)
    
    topic_word = model.topic_word_
    
    topics = []    
    
    for i, topic_dist in enumerate(topic_word):
        topic_words = np.array(vocab_np)[np.argsort(topic_dist)][:-(n_top_words+1):-1]
        topic = ' '.join(topic_words).encode('utf-8')
        topics.append(topic)
        print('Topic {}: {}'.format(i+1, topic))
        
    return topics
        
if __name__ == '__main__':
    docs = [
        ['python', 'text', 'data', 'nlp', 'data', 'matrix', 'mining'],
        ['data', 'science', 'data', 'processing', 'cleaning', 'data'],
        ['r', 'data', 'science', 'text', 'mining', 'nlp'],
        ['programming', 'c', 'algorithms', 'data', 'structures'],
    ]
    GetNTopics(docs, 5, 3)
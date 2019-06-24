# -*- coding: utf-8 -*-
"""seq2seq.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1EjOoPpfD-K-TNvvZh_yGGmLZgncNMjGq
"""

from google.colab import drive
drive.mount("/content/gdrive")

import string 
import re 
from numpy import array, argmax, random, take 
import pandas as pd 
from keras.models import Sequential 
from keras.layers import Dense, LSTM, Embedding, RepeatVector
from keras.preprocessing.text import Tokenizer
from keras.callbacks import ModelCheckpoint 
from keras.preprocessing.sequence import pad_sequences
from keras.models import load_model 
from keras import optimizers 
import matplotlib.pyplot as plt
from keras.layers import Dropout
# % matplotlib inline 
pd.set_option('display.max_colwidth', 200)
from keras import regularizers

df = pd.read_csv('gdrive/My Drive/Colab Notebooks/deu-eng/deu.txt', sep="\t", header=None)

#df.head()

#df.shape

df.columns = ['english', 'german']

for each in df.columns:
  df[each] = df[each].str.lower()

df['eng_totalwords'] = df['english'].str.split().str.len()
df['ger_totalwords'] = df['german'].str.split().str.len()

elen = df.eng_totalwords.unique().tolist()
glen = df.ger_totalwords.unique().tolist()

#max(elen), max(glen)

# function to build a tokenizer 
def tokenization(lines): 
      tokenizer = Tokenizer() 
      tokenizer.fit_on_texts(lines) 
      return tokenizer

# prepare english tokenizer 
eng_tokenizer = tokenization(df['english']) 
eng_vocab_size = len(eng_tokenizer.word_index) + 1 
eng_length = 101

print('English Vocabulary Size: %d' % eng_vocab_size)

# prepare Deutch tokenizer 
deu_tokenizer = tokenization(df['german']) 
deu_vocab_size = len(deu_tokenizer.word_index) + 1 
deu_length = 101

print('Deutch Vocabulary Size: %d' % deu_vocab_size)

def encode_sequences(tokenizer, length, lines):          
         # integer encode sequences          
         seq = tokenizer.texts_to_sequences(lines)          
         # pad sequences with 0 values          
         seq = pad_sequences(seq, maxlen=length, padding='post')           
         return seq

from sklearn.model_selection import train_test_split 

# split data into train and test set 
train,test= train_test_split(df[['english', 'german']],test_size=0.2,random_state= 12)

train, valid = train_test_split(train,test_size=0.2,random_state= 12)

trainX = encode_sequences(deu_tokenizer, deu_length, train['german']) 
trainY = encode_sequences(eng_tokenizer, eng_length, train['english']) 

#prepare validation data
validX = encode_sequences(deu_tokenizer, deu_length, valid['german']) 
validY = encode_sequences(eng_tokenizer, eng_length, valid['english']) 


# prepare test data 
testX = encode_sequences(deu_tokenizer, deu_length, test['german']) 
testY = encode_sequences(eng_tokenizer, eng_length, test['english'])

model = Sequential()
model.add(Embedding(deu_vocab_size, 512, input_length = deu_length, mask_zero=True))
model.add(LSTM(512))
model.add(Dropout(0.3))
model.add(RepeatVector(eng_length)) 
model.add(LSTM(512, return_sequences=True))
model.add(Dropout(0.3))
model.add(Dense(eng_vocab_size, activation='softmax', kernel_regularizer=regularizers.l2(0.01))) 
model.compile(optimizer=optimizers.RMSprop(lr=0.001), loss='sparse_categorical_crossentropy')

filename = 'saved_model' 

# set checkpoint
checkpoint = ModelCheckpoint(filename, monitor='val_loss',  
                             verbose=1, save_best_only=True, 
                             mode='min') 


# train model 
history = model.fit(trainX, trainY.reshape(trainY.shape[0], trainY.shape[1], 1), 
                    epochs=30, batch_size=1024, validation_data=(validX, validY.reshape(validX.shape[0], validY.shape[1], 1)), 
                   verbose=1)

plt.plot(history.history['loss']) 
plt.plot(history.history['val_loss']) 
plt.legend(['train','validation']) 
plt.show()

#model = load_model('saved_model')
preds = model.predict_classes(testX.reshape((testX.shape[0], testX.shape[1])))

def get_word(n, tokenizer):  
      for word, index in tokenizer.word_index.items():                       
          if index == n: 
              return word 
      return None

preds_text = [] 
for i in preds:        
       temp = []        
       for j in range(len(i)):             
            t = get_word(i[j], eng_tokenizer)             
            if j > 0:                 
                if (t==get_word(i[j-1],eng_tokenizer))or(t== None):                       
                     temp.append('')                 
                else:                      
                     temp.append(t)             
            else:                    
                if(t == None):                                   
                     temp.append('')                    
                else:                           
                     temp.append(t)        
       preds_text.append(' '.join(temp))

pred_df = pd.DataFrame({'actual' : test[:,0], 'predicted' : 
                        preds_text})

pred_df.sample(15)

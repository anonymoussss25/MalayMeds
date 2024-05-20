import pandas as pd
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import numpy as np
import pickle

url = 'C:/Users/hanan/Desktop/FYP Sem Break/FYP_MalayMedsdb1/datasets/dataset5symp_5rows_.csv'
df = pd.read_csv(url)

col_names = df.columns
for c in col_names:
    df[c] = df[c].replace("", 0)
category_col = ['Disease', 'Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4', 'Symptom_5']

labelEncoder = preprocessing.LabelEncoder()
mapping_dict={} 
for col in category_col:
    df[col] = labelEncoder.fit_transform(df[col])
    le_name_mapping = dict(zip(labelEncoder.classes_, labelEncoder.transform(labelEncoder.classes_)))
    mapping_dict[col]=le_name_mapping
print(mapping_dict)

X = df.iloc[:, 1:].values
Y = df['Disease'].values
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, max_depth=15, min_samples_leaf=1) # max_depth=6
model.fit(X_train, y_train)
y_pred_rf = model.predict(X_test)
print("Random Forest \nAccuracy is ", accuracy_score(y_test, y_pred_rf) * 100)
pickle.dump(model, open("model.pkl", "wb"))
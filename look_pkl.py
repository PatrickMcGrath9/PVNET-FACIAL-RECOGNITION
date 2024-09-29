import pickle


with open('encodings.pkl', 'rb') as f:
    data = pickle.load(f)

print(data)
from sklearn.ensemble import RandomForestClassifier
from music21 import *
import statistics as stats
import random
from music_generator import MusicGenerator
import os
# Data preprocessing was heavily inspired by:
# https://github.com/Skuldur/Classical-Piano-Composer/blob/master/lstm.py

# Random Forrest has to be fitted with two arrays:
# X: [n_samples, n_features]
# Y: [n_samples]

# We'll be representing the notes by integers
# A -> 0, B -> 1, etc.
# To do this, we'll need a "vocabulary" of all the notes
# and chords that show up in the training set

# NOTE: We'll have to somehow be able to deal with
# notes/chords we have never seen (might appear in
# the test set) => how??

# TODO
# ----
# * How to predict offsets between notes? Duration?
# * Which parts do we want to pick? (Soprano, Alto, etc.)
# * Which music to train on?
# * Incorporate multiple voices
#     - We could train on each one individually and then just stack them
#     - We could generate one, then generate the second one GIVEN the first one, etc.

def get_music21_notes(songs, voice='soprano'):
  '''
  Takes in a list of songs (e.g. "Bach") and parses each one.
  Currently, we take the first 'part' of the song and return
  all its notes and chords.

  Returns
  -------
  notes_to_parse: list of Music21 Notes and Chords
  '''
  notes_to_parse = []
  for song in songs:
    parsed_song = corpus.parse(song)
    # We probably want to make this more flexible so
    # it can take in the part we want?
    part = parsed_song.parts.stream()[voice]
    notes_to_parse.append([note for note in part.flat.notes])

  return notes_to_parse

def get_parsed_notes(music21_notes):
  '''
  Takes in the notes and chords that are music21
  classes as a 2D list (collection of notes for each song
  in the training data).

  Returns
  -------
  notes: list of Note and Chord representations that are hashable
  '''
  notes = []
  for note_group in music21_notes:
    notes.append([])
    for sound in note_group:
      if isinstance(sound, note.Note):
        notes[-1].append(str(sound.pitch))
      elif isinstance(sound, chord.Chord):
        notes[-1].append('.'.join(str(n) for n in sound.normalOrder))

  # [Jens]: I don't think we need normalization here, since all
  # of our features are already on the same scale.

  return notes

def make_dataset(parsed_notes, note_to_idx, sequence_length=10):
  '''
  Takes in the parsed notes, which is a 2D list of notes
  for all the songs in the training data.

  Returns
  -------
  X: [[sequence_length], [sequence_length], ...] (number of notes - sequence length times)
  Y: [number of notes - sequence length]
  '''
  X = []
  Y = []
  for song in parsed_notes:
    int_notes = list(map(lambda t: note_to_idx[t], song))
    for i in range(len(int_notes) - sequence_length):
      X.append(int_notes[i:i + sequence_length])
      Y.append(int_notes[i + sequence_length])

  return (X, Y)

def train_rf(X, Y, estimators=100):
  '''
  Train a Random Forest classifier on the dataset

  Returns
  -------
  clf: the trained Random Forest classifier
  '''
  clf = RandomForestClassifier(n_estimators=estimators)
  clf.fit(X, Y)

  return clf

def get_baseline_prediction(test_music, vocab, note_to_idx, start_length=10):
  '''
  TODO
  '''
  notes = get_parsed_notes(get_music21_notes(test_music))[0]
  predicted = notes[0: start_length]
  vocab = list(vocab)

  for i in range(len(notes) - start_length):
    random_note = vocab[random.randint(0, len(vocab)-1)]
    predicted.append(random_note)

  return predicted 
"""
def get_base_range_prediction(test_music, vocab, note_to_idx, start_length=10):
  '''
  Function to return a baseline prediction given a range of notes
  acquired from the training set
  '''
  notes = get_parsed_notes(get_music21_nootes(test_music))[0]
  predicted = notes[0: start_length]
  vocab = list(vocab)

  for i in range()
"""

def get_predictions(test_music, clf, note_to_idx, idx_to_note, start_length=10, num_chances=1):
  '''
  Starts with the first 'start_length' notes of the test_music
  and predicts from then on. Every predicted note/chord is appended
  and used for the next prediction (sliding window).

  num_chances: the number of predicted classes that will go into
              the accuracy calculation
  Returns
  -------
  predicted: the newly predicted song (including start sequence)
            this array will return num_chances possible notes for every prediction
  '''
  notes = get_parsed_notes(get_music21_notes(test_music))[0]
  int_notes = list(map(lambda t: note_to_idx[t], notes))
  predicted = int_notes[0: start_length]

  
  # previous impl, with only one hit/miss
  for i in range(len(int_notes) - start_length):
    prediction = clf.predict([predicted[i: i + start_length]])[0]
    predicted.append(prediction)

  return list(map(lambda t: idx_to_note[t], predicted))

"""
def get_predictions_accuracy(test_music, clf, note_to_idx, idx_to_note, start_length=10, num_chances=1):
  '''
  Starts with the first 'start_length' notes of the test_music
  and predicts from then on. Every predicted note/chord is appended
  and used for the next prediction (sliding window).

  num_chances: the number of predicted classes that will go into
              the accuracy calculation
  Returns
  -------
  predicted: the newly predicted song (including start sequence)
            this array will return num_chances possible notes for every prediction
  '''
  notes = get_parsed_notes(get_music21_notes(test_music))[0]
  int_notes = list(map(lambda t: note_to_idx[t], notes))
  predicted = int_notes[0: start_length]

  
  # previous impl, with only one hit/miss
  for i in range(len(int_notes) - start_length):
    prediction = clf.predict([predicted[i: i + start_length]])[0]
    predicted.append(prediction)

  return list(map(lambda t: idx_to_note[t], predicted))
"""

def play_music(predicted):
  '''
  Convert the predicted output into a midi file
  Literal copy of https://github.com/Skuldur/Classical-Piano-Composer/blob/master/lstm.py
  We're probably going to want to adjust this one to have different offsets etc.
  '''
  offset = 0
  output_notes = []

  # create note and chord objects based on the values generated by the model
  for pattern in predicted:
      # pattern is a chord
      if ('.' in pattern) or pattern.isdigit():
          notes_in_chord = pattern.split('.')
          notes = []
          for current_note in notes_in_chord:
              new_note = note.Note(int(current_note))
              new_note.storedInstrument = instrument.Piano()
              notes.append(new_note)
          new_chord = chord.Chord(notes)
          new_chord.offset = offset
          output_notes.append(new_chord)
      # pattern is a note
      else:
          new_note = note.Note(pattern)
          new_note.offset = offset
          new_note.storedInstrument = instrument.Piano()
          output_notes.append(new_note)

      # increase offset each iteration so that notes do not stack
      offset += 0.5

  midi_stream = stream.Stream(output_notes)
  midi_stream.show()

def get_music_data(datasetNum):
  '''
  Load the Bach corpus and split the data into training and test.
  '''
  bach_songs = corpus.getComposer('bach')
  song_list = []
  trained_songs = 1
  idx = 0
  while trained_songs < datasetNum:
    
    song = None
    if(os.name == 'posix'):
      song = 'bach/' + '.'.join(str(bach_songs[idx]).split('/')[-1].split('.')[:-1])
    else:
      song = 'bach/' + '.'.join(str(bach_songs[idx]).split('\\')[-1].split('.')[:-1])
    
    # Check if Soprano voice exits
    parsed_song = corpus.parse(song)

    # Hack to test if the song has a soprano voice
    try:
      part = parsed_song.parts.stream()['soprano']
      song_list.append(song)
      trained_songs += 1
    except:
      pass
    idx += 1

  # Randomize the songs before making training and test split
  random.shuffle(song_list)

  index_split = int(datasetNum * .8)
  return (song_list[:index_split], song_list[index_split:])

def get_accuracy(music, clf, note_to_idx, idx_to_note, num_chances=1):
  '''
  Calculate training/testing accuracy based on "right or wrong" evaluation
  criterion.

  Returns
  -------
  Mean of training/testing accuracy for each song in the training set
  '''
  accuracies = []
  for song in music:
    # Get original
    original = get_parsed_notes(get_music21_notes([song]))[0]
    # Get predicted
    predicted = get_predictions([song], clf, note_to_idx, idx_to_note)
    count = 0
    for note1, note2 in zip(predicted[10:], original[10:]):
      if note1 == note2:
        count += 1
      
    accuracies.append(count/len(original[10:]))

  return stats.mean(accuracies)

def main():
  # Get training and test set
  training_music, test_music = get_music_data(200)

  # Parse training music into notes
  music21_notes_train = get_music21_notes(training_music)
  parsed_notes_train = get_parsed_notes(music21_notes_train)

  # Parse test music into notes
  music21_notes_test = get_music21_notes(test_music)
  parsed_notes_test = get_parsed_notes(music21_notes_test)

  # Create the vocabulary
  # NOTE: To avoid missing key errors, we add all notes from the
  #       testing set also in the vocab.
  vocab = set(note for group in parsed_notes_train for note in group)
  for group in parsed_notes_test:
    for note in group:
      vocab.add(note)

  #print('vocab', vocab)

  # Create note to int and int to note mappings
  note_to_idx = {note: idx for idx, note in enumerate(vocab)}
  idx_to_note = {idx: note for note, idx in note_to_idx.items()}

  # Create the dataset with notes X and labels Y
  X, Y = make_dataset(parsed_notes_train, note_to_idx)
  #print("Test notes: {}".format(parsed_notes_test))

  # Traing the classifier
  clf = train_rf(X, Y)

  # Get the training accuracy
  print("Training Accuracy")
  print("-----------------")
  training_accuracy = get_accuracy(training_music, clf, note_to_idx, idx_to_note)
  print(training_accuracy)

  # print()

  # Get the test accuracy
  print("Test Accuracy")
  print("-----------------")
  test_accuracy = get_accuracy(test_music, clf, note_to_idx, idx_to_note)
  print(test_accuracy)

  # Pick a random song from the test set which we
  # want to listen to
  show_song = test_music[random.randint(0, len(test_music)-1)]

  # Predicted on the randomly picked song
  predicted = get_predictions([show_song], clf, note_to_idx, idx_to_note)

  # set the vocab for the baseline based on the first 10 notes of the test set
  notes = get_parsed_notes(get_music21_notes(test_music))[0]
  baseline_vocab = set(notes[0:10])

  # Get baseline prediction
  baseline_predicted = get_baseline_prediction([show_song], baseline_vocab, note_to_idx)
  # print(baseline_predicted)

  # Open the song in MuseScore
  # play_music(predicted)
  # play_music(baseline_predicted)

if __name__ == "__main__":
  main()
 
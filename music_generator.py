from sklearn.ensemble import RandomForestClassifier
from music21 import * 

class MusicGenerator():
  def __init__(self, training_music, test_music):
    self.training_music = training_music
    self.test_music = test_music

  def generate_music(self):
    '''
    TODO
    '''
    music21_notes = self.get_music21_notes()
    parsed_notes = self.get_parsed_notes(music21_notes)

    self.vocab = set(note for group in parsed_notes for note in group)
    self.note_to_idx = {note: idx for idx, note in enumerate(self.vocab)}
    self.idx_to_note = {idx: note for note, idx in self.note_to_idx.items()}

    X, Y = self.make_dataset(parsed_notes)
  
    clf = self.train_rf(X, Y)

    predicted = self.get_predictions(clf)
    return predicted

  def get_music21_notes(self, voice='soprano'):
    '''
    Takes in a list of songs (e.g. "Bach") and parses each one.
    Currently, we take the first 'part' of the song and return
    all its notes and chords. 

    Returns
    -------
    notes_to_parse: list of Music21 Notes and Chords 
    '''
    notes_to_parse = []
    for song in self.training_music: 
      parsed_song = corpus.parse(song)
      # We probably want to make this more flexible so 
      # it can take in the part we want? 
      part = parsed_song.parts.stream()[voice]
      notes_to_parse.append([note for note in part.flat.notes])

    return notes_to_parse

  def get_parsed_notes(self, music21_notes):
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

  def make_dataset(self, parsed_notes, sequence_length=10):
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
      int_notes = list(map(lambda t: self.note_to_idx[t], song))
      for i in range(len(int_notes) - sequence_length):
        X.append(int_notes[i:i + sequence_length])
        Y.append(int_notes[i + sequence_length])

    return (X, Y)

  def train_rf(self, X, Y, estimators=100):
    '''
    Train a Random Forest classifier on the dataset 

    Returns
    -------
    clf: the trained Random Forest classifier 
    '''
    clf = RandomForestClassifier(n_estimators=estimators)
    clf.fit(X, Y)

    return clf 

  def get_predictions(self, clf, start_length=10):
    '''
    Starts with the first 'start_length' notes of the test_music
    and predicts from then on. Every predicted note/chord is appended
    and used for the next prediction (sliding window).

    Returns
    -------
    predicted: the newly predicted song (including start sequence)
    '''
    notes = self.get_parsed_notes(self.get_music21_notes())[0]
    int_notes = list(map(lambda t: self.note_to_idx[t], notes))
    predicted = int_notes[0: start_length]

    for i in range(len(int_notes) - start_length):
      prediction = clf.predict([predicted[i: i + start_length]])[0]
      predicted.append(prediction)

    return list(map(lambda t: self.idx_to_note[t], predicted))
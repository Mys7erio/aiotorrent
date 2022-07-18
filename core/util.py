def chunk(string, size):
	"""A function that splits a string into specified chunk size

		string: str
			The string to be broken / chunked down
		size: int
			The size of each chunk
	"""

	for _ in range(0, len(string), size):
		yield string[:size]
		string = string[size:]



if __name__ == "__main__":
	a = 'abcabcabcabcabcabcabcabcabcabc'
	for i in chunk(a, 7):
		print(i)
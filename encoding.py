# Open the file in binary mode for reading
with open('my_file.bin', 'rb') as file:
    # Read the contents of the file as bytes
    my_bytes = file.read()

    # Decode the bytes using UTF-8
    decoded_string = my_bytes.decode('utf-8')

print(decoded_string)
import face_recognition

# Load the images




img1 = face_recognition.load_image_file("vijay.jpg")
img2 = face_recognition.load_image_file("shashank.jpg")

# Generate face encodings for each image
# print(face_recognition.face_encodings(img1))
img1_encoding = face_recognition.face_encodings(img1)[0]
img2_encoding = face_recognition.face_encodings(img2)[0]

# Compare the face encodings and get a boolean value indicating if they match
result = face_recognition.compare_faces([img1_encoding], img2_encoding)

# Print the result
if result[0]:
    print("The two images are of the same person.")
else:
    print("The two images are of different people.")
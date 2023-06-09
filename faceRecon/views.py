from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import connections
from .forms import UserSelection
from django.shortcuts import render
from django.shortcuts import render
from django.db import connection
from django.core.files.storage import FileSystemStorage
from io import BytesIO
from django.http import HttpResponse
import pytesseract
from PIL import Image
import face_recognition
import ocr
import io
import cv2
import numpy as np
import os

BASE_DIR = getattr(settings, 'BASE_DIR')

def index(request):
    context = {'forms': UserSelection }
    return render(request, 'index.html', context)

def create_dataset(request):
    if request.method == "POST":
        face_id = int(request.POST['selected_user'])
        #print("Face ID->", face_id, type(face_id))

        cam = cv2.VideoCapture(0)
        cam.set(3, 640)  # set video width
        cam.set(4, 480)  # set video height
        face_detector = cv2.CascadeClassifier(BASE_DIR + '/ml/haarcascade_frontalface_default.xml')  # For each person, enter one numeric face id
        print("[INFO] Initializing face capture. Look the camera and wait ...")  # Initialize individual sampling face count
        count = 0
        while (True):
            ret, img = cam.read()
            # img = cv2.flip(img, -1) # flip video image vertically
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.3, 5)

            # Skip the process if multiple faces detected:
            if len(faces) == 1:
                for (x, y, w, h) in faces:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    count += 1
                    # Save the captured image into the datasets folder
                    cv2.imwrite(BASE_DIR+"/ml/dataset/User." + str(face_id) + '.' +
                                str(count) + ".jpg", img[y:y + h, x:x + w])
                    cv2.waitKey(250)

                cv2.imshow('Face', img)
                k = cv2.waitKey(1) & 0xff  # Press 'ESC' for exiting video
                if k == 27:
                    break
                elif count >= 30:  # Take 30 face sample and stop video
                    break  # Do a bit of cleanup
                print(count)
            else:
                print("\n multiple faces detected")

        print("\n [INFO] Exiting Program and cleanup stuff")
        cam.release()
        cv2.destroyAllWindows()

        messages.success(request, 'Face successfully registered.')

    else:
        print("Its a GET method.")

    return redirect('/')

def detect(request):
    faceDetect = cv2.CascadeClassifier(BASE_DIR + '/ml/haarcascade_frontalface_default.xml')

    cam = cv2.VideoCapture(0)
    # creating recognizer
    rec = cv2.face.LBPHFaceRecognizer_create();
    # loading the training data
    rec.read(BASE_DIR + '/ml/recognizer/trainer.yml')
    getId = 0
    font = cv2.FONT_HERSHEY_SIMPLEX
    userId = 0
    while (True):
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = faceDetect.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

            getId, conf = rec.predict(gray[y:y + h, x:x + w])  # This will predict the id of the face
            print(getId, conf)
            confidence = "  {0}%".format(round(100 - conf))
            # print conf;
            if conf < 35:
                try:
                    user = User.objects.get(id=getId)
                except  User.DoesNotExist:
                    pass

                print("User Name", user.username)

                userId = getId
                if user.username:
                    cv2.putText(img, user.username, (x+5, y+h-10), font, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(img, "Detected", (x, y + h), font, 1, (0, 255, 0), 2)
            else:
                cv2.putText(img, "Unknown", (x, y + h), font, 1, (0, 0, 255), 2)

            cv2.putText(img, str(confidence), (x + 5, y - 5), font, 1, (255, 255, 0), 1)
            # Printing that number below the face
            # @Prams cam image, id, location,font style, color, stroke

        cv2.imshow("Face", cv2.cvtColor(img, cv2.COLOR_BGR2RGB))  # convert BGR to RGB for display
        if (cv2.waitKey(1) == ord('q')):
            break
        #elif (userId != 0):
        #    cv2.waitKey(1000)
        #    cam.release()
        #    cv2.destroyAllWindows()
        #    return redirect('/records/details/' + str(userId))

    cam.release()
    cv2.destroyAllWindows()
    return redirect('/')

def trainer(request):
    '''
        In trainer.py we have to get all the samples from the dataset folder,
        for the trainer to recognize which id number is for which face.

        for that we need to extract all the relative path
        i.e. dataset/user.1.1.jpg, dataset/user.1.2.jpg, dataset/user.1.3.jpg
        for this python has a library called os
    '''

    # Path for face image database
    path = BASE_DIR + '/ml/dataset'
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(BASE_DIR+"/ml/haarcascade_frontalface_default.xml")

    def getImagesAndLabels(path):
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        faceSamples = []
        ids = []
        for imagePath in imagePaths:
            PIL_img = Image.open(imagePath)  # color
            img_numpy = np.array(PIL_img, 'uint8')
            id = int(os.path.split(imagePath)[-1].split(".")[1])
            faceSamples.append(img_numpy)
            ids.append(id)
            # print ID
            cv2.imshow("training", img_numpy)
            cv2.waitKey(10)
        return np.array(faceSamples), np.array(ids)

    print("[INFO] Training faces. It will take a few seconds. Wait ...")
    faces, ids = getImagesAndLabels(path)
    recognizer.train(faces, ids)
    recognizer.save(BASE_DIR+'/ml/recognizer/trainer.yml')
    print("[INFO] {0} faces trained. Exiting Program".format(len(np.unique(ids))))
    cv2.destroyAllWindows()
    messages.success(request, "{0} faces trained successfully".format(len(np.unique(ids))))
    return redirect('/')


def match(request):
    with connections['default'].cursor() as cursor:
        cursor.execute('SELECT photograph FROM aadhaar_details')
        my_data = []
        for row in cursor:
            if row[0] is not None:
                nparr = np.frombuffer(row[0], np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # decode as a colored image
                filename = 'image_' + str(cursor.rowcount) + '.png'
                cv2.imwrite(filename, img)
                my_data.append({'filename': filename, 'img': img})
    return render(request, "match.html", {'my_data': my_data})
import mysql.connector

def fetch(request):
    if request.method == 'POST':
        try:
            image = request.FILES['image']
            img = Image.open(image)
            fs = FileSystemStorage()
            filename = fs.save("uploads/"+image.name, image)
            uploaded_file_url = fs.url(filename)
            def checkIfLegit(folder_path):
                images = []
                for filename in os.listdir(folder_path):
                    if filename.endswith('.jpg') or filename.endswith('.png'):
                        img_path = os.path.join(folder_path, filename)
                        img = face_recognition.load_image_file(img_path)
                        images.append(img)
                return images
            images = checkIfLegit(BASE_DIR + "/ml/dataset/")
            img1 = face_recognition.load_image_file(uploaded_file_url)
            for img2 in images:
                img1_encoding = face_recognition.face_encodings(img1)[0]
                img2_encoding = face_recognition.face_encodings(img2)[0]

                # Compare the face encodings and get a boolean value indicating if they match
                result = face_recognition.compare_faces([img1_encoding], img2_encoding)

                if result[0]:
                    print("The two images are of the same person.")
                    return render(request,'fetch.html',{'data':True})

                else:
                    print("The two images are of different people.")
                    return render(request,'fetch.html',{'data':False})
                    
        except Exception as e:
            print(e)
    return render(request, 'fetch.html',{"data":"none"})

def image_data_view(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM image_data')
        rows = cursor.fetchall()
    return render(request, 'image_data.html', {'rows': rows})

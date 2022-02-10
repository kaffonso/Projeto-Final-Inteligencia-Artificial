from PIL import Image, ImageTk
import pytesseract
from gtts import gTTS
import cv2
import PySimpleGUI as sg
import os
from playsound import playsound as play

tessdata_dir_config = "data"

sg.theme('TanBlue')

layout = [
  [sg.Text('Insira uma imagem:', font=('verdana',10)), sg.Input(size=(46,5), key='file', font=('verdana',10)),sg.FileBrowse(font=('verdana',10))],
  [sg.Column([[sg.Image(key='image')]], justification= 'center')],
  [sg.Text("Texto extraido:", font=('verdana',10))], 
  [sg.Multiline(
    key='textarea', 
    size=(60,5), 
    no_scrollbar=True, 
    auto_size_text=True, 
    justification="center", 
    font=('Verdana',12),
    pad=10)],
  [sg.Text("Precisao por linha:", font=('verdana',10))], 
  [sg.Multiline(
    key='confidence', 
    size=(75,2), 
    no_scrollbar=True, 
    auto_size_text=True, 
    justification="center", 
    font=('Verdana',10),
    pad=10)],
  [sg.Column([[sg.Button('Converter', font=('verdana',10), size=(21,1)), sg.Button('Ouvir', font=('verdana',10), size=(21,1)), sg.Button('RealTime', font=('verdana',10), size=(21,1))]], 
  justification= 'center')]
  ]

window =  sg.Window('Extrator de Texto de Imagens',layout, margins=(20,5))

while True:
  event, value = window.read()

  if event == sg.WINDOW_CLOSED:
    break

  if event == 'Converter':
    filename = value['file']
    if os.path.exists(filename): 
      img = cv2.imread(filename)

      im = Image.open(filename)
      im = im.resize((300,250), resample=Image.ANTIALIAS)
      image = ImageTk.PhotoImage(image=im)
      
      gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
      blr = cv2.GaussianBlur(gry, (3, 3), 0)
      img_filtered = cv2.threshold(blr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

      output = pytesseract.image_to_string(img_filtered)  
      dataframe = pytesseract.image_to_data(img_filtered,output_type='data.frame')
    
      dataframe = dataframe[dataframe.conf != -1]
      lines = dataframe.groupby(['page_num','block_num','par_num', 'line_num'])['text'].apply(lambda x : ' '.join(list(x))).tolist()
      confidences = dataframe.groupby(['page_num','block_num','par_num', 'line_num'])['conf'].mean().tolist()
      line_confidences = []
      for i in range(len(lines)):
        if lines[i].strip():
          line_confidences.append(((lines[i]), round(confidences[i],1)))
    
      window['textarea'].Update(output)
      window['confidence'].Update(line_confidences)
      window['image'].Update(data=image)

      audio = gTTS(text = output, lang = 'en', slow = False)
      audio.save("audio.mp3")

  if event == 'Ouvir':
    play("audio.mp3")

  if event == 'RealTime':
    cap = cv2.VideoCapture(0)
    widthScreen = 640     
    heigthScreen = 480

    cap.set(3,widthScreen)
    cap.set(4,heigthScreen)

    font_scale = 1.5
    font = cv2.FONT_HERSHEY_SIMPLEX

    while True:
      Success, img = cap.read()
      imgH, imgW, _ = img.shape   
      x1, y1, w1, h1 =  0, 0, imgH, imgW

      gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
      blr = cv2.GaussianBlur(gry, (3, 3), 0)
      img_filtered = cv2.threshold(blr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

      outputChar = pytesseract.image_to_string(img_filtered)
      outputBoxes = pytesseract.image_to_boxes(img_filtered)

      for boxes in outputBoxes.splitlines(): 
        boxes = boxes.split(' ')
        x,y,w,h = int(boxes[1]), int(boxes[2]), int(boxes[3]), int(boxes[4])  
        cv2.rectangle(img, (x,imgH-y), (w,imgH-h), (0,0,255),1)

      if outputChar.isspace():
        print('Imagem sem texto!\n')
      else:
        #print('Texto extraido: '+ outputChar)
        outputChar = outputChar.replace("?" , " ")
        cv2.putText(img, outputChar, (x1 + int(w1/10), y1 + int(h1/10)), font, 1, (0,0,255), 2)
  
      cv2.imshow("Image", img)
      if cv2.waitKey(2) & 0XFF == ord('q'):
         break

    cap.release()
    cv2.destroyAllWindows()

  
window.close()
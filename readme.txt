Vào cmd sử dụng những phân cần thiết

# Navigate to your project folder// download file ở đâu thì địa chỉ nó ở đó
cd C:\...\...\NCKH\Personalize learning

# Nếu làm lần đầu
$ python -m venv venv
$ venv\Scripts\activate
$ python -m pip install -r requirements.txt
$ python manage.py makemigrations
$ python manage.py migrate
$ python manage.py runserver

#Nếu lần 2
$ venv\Scripts\activate
$ python manage.py runserver
# Sample Django App (Airport Catalog) #

## Fast development deploy ##

    cd /your/path/
    git clone git://github.com/lexqt/aircat.git
    virtualenv aircat
    cd aircat
    bin/pip install -r requirements.txt
    echo -e "DEBUG=True\nSECRET_KEY='your_key'" > aircat/aircat/localsettings.py
    bin/python aircat/manage.py syncdb
    bin/python aircat/manage.py importdata --buffer 100 airports.dat
    bin/python aircat/manage.py runserver localhost:8000

And open http://localhost:8000/

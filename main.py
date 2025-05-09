import requests
from bs4 import BeautifulSoup
import getpass

# Lietotāja ievade
username = input("Ievadi ORTUS lietotājvārdu: ")
password = getpass.getpass("Ievadi paroli: ")

# Sesija, lai saglabātu autentifikācijas stāvokli
session = requests.Session()

# ORTUS sākumlapa vai autentifikācijas URL (fiktīvs piemērs)
login_url = 'https://ortus.lu.lv/login/index.php'

# Atkarībā no ORTUS autentifikācijas sistēmas šie lauki var būt dažādi
payload = {
    'username': username,
    'password': password
}

# Autorizācija
response = session.post(login_url, data=payload)

# Pārbaudām, vai autorizācija bija veiksmīga
if "Nederīgs lietotājvārds vai parole" in response.text or response.url == login_url:
    print("Autorizācija neizdevās. Pārbaudi datus.")
else:
    print("Autorizācija veiksmīga!")

    # Iet uz atzīmju lapu – piemērs!
    grades_url = 'https://estudijas.lu.lv/my/grades.php'
    grades_response = session.get(grades_url)

    # Parsējam HTML ar BeautifulSoup
    soup = BeautifulSoup(grades_response.text, 'html.parser')

    # Šeit ir atkarīgs no faktiskās HTML struktūras
    print("\nTavas atzīmes:")
    for row in soup.select('table.grades tr'):
        columns = row.find_all('td')
        if columns:
            course = columns[0].get_text(strip=True)
            grade = columns[1].get_text(strip=True)
            print(f"{course}: {grade}")

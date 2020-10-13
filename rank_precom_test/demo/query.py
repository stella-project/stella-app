import requests


def main():
    results = requests.get('http://0.0.0.0:5000/index')
    print(results.text)

    query = 'kaffeemaschine'
    results = requests.get('http://0.0.0.0:5000/ranking?query=' + query)
    print(results.text)

    query = 'china'
    results = requests.get('http://0.0.0.0:5000/ranking?query=' + query)
    print(results.text)

    query = 'chna'
    results = requests.get('http://0.0.0.0:5000/ranking?query=' + query)
    print(results.text)

    query = 'kaffeemaschine'
    page = 4
    rpp = 100
    results = requests.get('http://0.0.0.0:5000/ranking?query=' + query + '&page=' + str(page) + '&rpp=' + str(rpp))
    print(results.text)


if __name__ == '__main__':
    main()
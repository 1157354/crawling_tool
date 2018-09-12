from app import app

if __name__ == '__main__':
    app.run(port=9998, debug=True, use_reloader=False)
    print('helloworld')

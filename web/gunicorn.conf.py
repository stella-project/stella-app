

def on_starting(server):
    print("Gunicorn master process is starting...")

def when_ready(server):
    from app.app import create_app, scheduler
    app = create_app()  # Create an instance of the app
    with app.app_context():
        if app.config["SENDFEEDBACK"]:
            print("Initializing and starting scheduler inside Gunicorn master process")
            scheduler.init_app(app)  # Initialize the scheduler
            scheduler.start()  # Start the scheduler

    print("Scheduler started in Gunicorn master process")

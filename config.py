class Config:
    SECRET_KEY = "super-secret-key"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/iosa_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
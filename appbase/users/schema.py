from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey

from appbase.sa import metadata, engine, Column_created, Column_id, Column_active


users = Table('users', metadata,
              Column_id(),
              Column('email', String, nullable=False, unique=True, index=True),
              Column('password', String),
              Column_created(),
              Column_active(),
              Column('fname', String, nullable=False),
              Column('lname', String)
              )

plans = Table('plans', metadata,
              Column_id(),
              Column_created(),
              Column_active(),
              Column('name', String, nullable=False),
              Column('description', String),
              )

subscriptions = Table('subscriptions', metadata,
                      Column_id(),
                      Column('user_id', None, ForeignKey('users.id')),
                      Column('plan_id', None, ForeignKey('plans.id')),
                      Column_created(),
                      Column('created_by', Integer),
                      Column('start_time', DateTime),
                      Column('end_time', DateTime),
                      )

metadata.create_all(engine)

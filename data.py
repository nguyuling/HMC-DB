import csv
from pymongo import MongoClient

client = MongoClient("mongodb+srv://dbAdmin:123abc@cluster0.iuvvkqs.mongodb.net/")
db = client["HMC"]

#! Patients Collection
collection = db["patients"]
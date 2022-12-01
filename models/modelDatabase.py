from pydantic import BaseModel

class registerElement(BaseModel):
    Pregnancies: float
    Glucose: float
    BloodPresure: float
    SkinThickness: float
    Insulin: float
    BMI: float
    DiabetesPedigreeFunction: float
    Age: float
    Outcome: float
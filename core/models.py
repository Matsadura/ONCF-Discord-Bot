from pydantic import BaseModel, Field
from typing import List, Optional

class Station(BaseModel):
    name: str
    code: str

class PassengerInfo(BaseModel):
    numeroClient: Optional[str] = None
    codeTarif: Optional[str] = None
    codeProfilDemographique: str = "3" # 3 = Default, 2 = Jeune
    dateNaissance: Optional[str] = None

class AvailabilityRequest(BaseModel):
    codeGareDepart: str
    codeGareArrivee: str
    codeNiveauConfort: int = 2
    dateDepartAller: str
    dateDepartAllerMax: Optional[str] = None
    dateDepartRetour: Optional[str] = None
    dateDepartRetourMax: Optional[str] = None
    isTrainDirect: Optional[bool] = None
    isPreviousTrainAller: Optional[bool] = None
    isTarifReduit: bool = True
    adulte: int = 1
    kids: int = 0
    listVoyageur: List[PassengerInfo]
    booking: bool = True
    isEntreprise: bool = False
    token: str = ""
    numeroContract: str = ""
    codeTiers: str = ""
    iTravel: bool = False
    isActive: bool = False

class Transfer(BaseModel):
    station_name: str
    arrival_time: str
    departure_time: str
    layover_minutes: int

class Fare(BaseModel):
    first_class_price: Optional[float] = None
    second_class_price: Optional[float] = None

class Journey(BaseModel):
    departure_station: str
    arrival_station: str
    departure_time: str
    arrival_time: str
    duration: str
    train_numbers: str
    fares: Fare
    transfers: List[Transfer] = []
    
    # Computed fields for sorting/display
    duration_minutes: int = 0
    min_price: float = float('inf')

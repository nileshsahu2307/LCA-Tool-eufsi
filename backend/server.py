from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import io
import tempfile
import shutil

# Authentication imports
from jose import JWTError, jwt
from passlib.context import CryptContext

# LCA Engine imports
import brightway2 as bw
from bw2data import projects, databases, methods, Database
from bw2io import bw2setup
import bw2calc as bc
import bw2analyzer
import numpy as np

# PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'lca_tool')

print(f"Connecting to MongoDB at: {mongo_url}")
print(f"Using database: {db_name}")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Create the main app
app = FastAPI(title="EUFSI LCA Tool API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# LCA project directory
BW_PROJECT_DIR = Path(tempfile.gettempdir()) / "lca_projects"
BW_PROJECT_DIR.mkdir(exist_ok=True)

# ============== AUTHENTICATION ==============

# JWT Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "eufsi-lca-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer(auto_error=False)

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    company: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict]:
    """Get current user from JWT token. Returns None if no valid token."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
        return user
    except JWTError:
        return None

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Require authentication - raises exception if not authenticated."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ============== MODELS ==============

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class FiberInput(BaseModel):
    material: str
    percentage: float
    production_location: str

class YarnInput(BaseModel):
    name: str
    count_nm: float
    percentage: float
    spinning_method: str
    fibers: List[FiberInput]

class FabricInput(BaseModel):
    name: str
    construction_method: str
    percentage: float
    finishing_method: str
    coloring_method: str
    color_depth: str
    yarns: List[str]  # References to yarn names

class ManufacturingInput(BaseModel):
    finish_treatments: List[str]
    cutting_waste_percentage: float
    waste_recycled_percentage: float
    waste_incinerated_percentage: float
    waste_landfilled_percentage: float

class ProductionLocations(BaseModel):
    spinning_location: str
    spinning_renewable_energy_percentage: float
    fabric_construction_location: str
    fabric_construction_renewable_energy_percentage: float
    finishing_location: str
    finishing_renewable_energy_percentage: float
    manufacturing_location: str
    manufacturing_renewable_energy_percentage: float

class TransportLeg(BaseModel):
    mode: str
    distance_km: float

class TransportInput(BaseModel):
    final_destination: str
    legs: List[TransportLeg]

class UsePhaseInput(BaseModel):
    include: bool
    washing_temperature: float
    drying_method: str
    ironing: bool
    lifetime_washing_cycles: int
    washing_transport_distance_km: float

class EndOfLifeInput(BaseModel):
    include: bool
    recycled_percentage: float
    incinerated_percentage: float
    landfill_percentage: float

class LCAProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    industry: str  # textile, footwear, construction, battery
    scope: str  # cradle-to-gate, cradle-to-grave, both
    database: str  # USLCI, Agribalyse, FORWAST
    method: str  # ReCiPe, EF3.1
    product_weight_grams: float
    product_scenario: str
    
class TextileInputData(BaseModel):
    yarns: List[YarnInput]
    fabrics: List[FabricInput]
    manufacturing: ManufacturingInput
    production_locations: ProductionLocations
    transport: TransportInput
    use_phase: UsePhaseInput
    end_of_life: EndOfLifeInput

class LCAProject(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    industry: str
    scope: str
    database: str
    method: str
    product_weight_grams: float
    product_scenario: str
    input_data: Optional[Dict[str, Any]] = None
    status: str = "draft"  # draft, calculating, completed, error
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LCAResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    method_name: str
    impact_categories: Dict[str, Any]
    contribution_by_stage: Dict[str, Dict[str, float]]
    total_impact: float
    unit: str
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== BRIGHTWAY2 ENGINE ==============

class Brightway2Engine:
    """Real Brightway2 LCA calculation engine"""
    
    AVAILABLE_DATABASES = {
        "USLCI": {
            "name": "US Life Cycle Inventory Database",
            "description": "Comprehensive US LCI data for manufacturing processes",
            "source": "NREL"
        },
        "Agribalyse": {
            "name": "Agribalyse",
            "description": "French agricultural and food LCI database",
            "source": "ADEME"
        },
        "FORWAST": {
            "name": "FORWAST",
            "description": "European waste treatment and resource database",
            "source": "EU Project"
        }
    }
    
    # Full ReCiPe/EF 3.1 impact categories
    IMPACT_CATEGORIES = {
        "ReCiPe": {
            "climate_change": ("ReCiPe Midpoint (H)", "climate change", "GWP100", "kg CO2 eq"),
            "ozone_depletion": ("ReCiPe Midpoint (H)", "ozone depletion", "ODP", "kg CFC-11 eq"),
            "terrestrial_acidification": ("ReCiPe Midpoint (H)", "terrestrial acidification", "TAP", "kg SO2 eq"),
            "freshwater_eutrophication": ("ReCiPe Midpoint (H)", "freshwater eutrophication", "FEP", "kg P eq"),
            "marine_eutrophication": ("ReCiPe Midpoint (H)", "marine eutrophication", "MEP", "kg N eq"),
            "human_toxicity": ("ReCiPe Midpoint (H)", "human toxicity", "HTPinf", "kg 1,4-DB eq"),
            "photochemical_oxidant_formation": ("ReCiPe Midpoint (H)", "photochemical oxidant formation", "POFP", "kg NMVOC"),
            "particulate_matter_formation": ("ReCiPe Midpoint (H)", "particulate matter formation", "PMFP", "kg PM10 eq"),
            "terrestrial_ecotoxicity": ("ReCiPe Midpoint (H)", "terrestrial ecotoxicity", "TETP", "kg 1,4-DB eq"),
            "freshwater_ecotoxicity": ("ReCiPe Midpoint (H)", "freshwater ecotoxicity", "FETP", "kg 1,4-DB eq"),
            "marine_ecotoxicity": ("ReCiPe Midpoint (H)", "marine ecotoxicity", "METP", "kg 1,4-DB eq"),
            "ionising_radiation": ("ReCiPe Midpoint (H)", "ionising radiation", "IRP_HE", "kg U235 eq"),
            "agricultural_land_occupation": ("ReCiPe Midpoint (H)", "agricultural land occupation", "ALOP", "m2a"),
            "urban_land_occupation": ("ReCiPe Midpoint (H)", "urban land occupation", "ULOP", "m2a"),
            "natural_land_transformation": ("ReCiPe Midpoint (H)", "natural land transformation", "NLTP", "m2"),
            "water_depletion": ("ReCiPe Midpoint (H)", "water depletion", "WDP", "m3"),
            "metal_depletion": ("ReCiPe Midpoint (H)", "metal depletion", "MDP", "kg Fe eq"),
            "fossil_depletion": ("ReCiPe Midpoint (H)", "fossil depletion", "FDP", "kg oil eq"),
        },
        "EF3.1": {
            "climate_change": ("EF 3.1", "climate change", "GWP", "kg CO2 eq"),
            "ozone_depletion": ("EF 3.1", "ozone depletion", "ODP", "kg CFC-11 eq"),
            "human_toxicity_cancer": ("EF 3.1", "human toxicity: cancer", "HT-c", "CTUh"),
            "human_toxicity_non_cancer": ("EF 3.1", "human toxicity: non-cancer", "HT-nc", "CTUh"),
            "particulate_matter": ("EF 3.1", "particulate matter", "PM", "disease incidence"),
            "ionising_radiation": ("EF 3.1", "ionising radiation", "IR", "kBq U235 eq"),
            "photochemical_ozone_formation": ("EF 3.1", "photochemical ozone formation", "POF", "kg NMVOC eq"),
            "acidification": ("EF 3.1", "acidification", "AP", "mol H+ eq"),
            "eutrophication_terrestrial": ("EF 3.1", "eutrophication: terrestrial", "EP-t", "mol N eq"),
            "eutrophication_freshwater": ("EF 3.1", "eutrophication: freshwater", "EP-fw", "kg P eq"),
            "eutrophication_marine": ("EF 3.1", "eutrophication: marine", "EP-m", "kg N eq"),
            "ecotoxicity_freshwater": ("EF 3.1", "ecotoxicity: freshwater", "ET-fw", "CTUe"),
            "land_use": ("EF 3.1", "land use", "LU", "Pt"),
            "water_use": ("EF 3.1", "water use", "WU", "m3 world eq"),
            "resource_use_minerals": ("EF 3.1", "resource use: minerals and metals", "RU-mm", "kg Sb eq"),
            "resource_use_fossils": ("EF 3.1", "resource use: fossils", "RU-f", "MJ"),
        }
    }
    
    # Textile activity mapping for Brightway2
    TEXTILE_ACTIVITY_MAPPING = {
        # Fiber production activities
        "Cotton fiber (Global)": {"name": "cotton fiber production", "unit": "kg"},
        "Cotton, organic (Global)": {"name": "cotton fiber production, organic", "unit": "kg"},
        "Polyester fiber (Global)": {"name": "polyester fiber production", "unit": "kg"},
        "Polyester, recycled (Global)": {"name": "polyester fiber production, recycled", "unit": "kg"},
        "Wool fiber (Global)": {"name": "wool production", "unit": "kg"},
        "Viscose fiber (Global)": {"name": "viscose fiber production", "unit": "kg"},
        "Lyocell fiber (Global)": {"name": "lyocell fiber production", "unit": "kg"},
        "Modal fiber (Global)": {"name": "modal fiber production", "unit": "kg"},
        "Elastane fiber (Global)": {"name": "elastane fiber production", "unit": "kg"},
        "Nylon fiber (Global)": {"name": "nylon fiber production", "unit": "kg"},
        "Acrylic fiber (Global)": {"name": "acrylic fiber production", "unit": "kg"},
        "Linen fiber (Global)": {"name": "flax fiber production", "unit": "kg"},
        "Hemp fiber (Global)": {"name": "hemp fiber production", "unit": "kg"},
        "Silk fiber (Global)": {"name": "silk production", "unit": "kg"},
        
        # Spinning processes - all variants from schema
        "Ring spinning": {"name": "yarn spinning, ring", "unit": "kg"},
        "Ring spinning for weaving, carded yarn": {"name": "yarn spinning, ring, weaving, carded", "unit": "kg"},
        "Ring spinning for weaving, combed yarn": {"name": "yarn spinning, ring, weaving, combed", "unit": "kg"},
        "Ring spinning for knitting, carded yarn": {"name": "yarn spinning, ring, knitting, carded", "unit": "kg"},
        "Ring spinning for knitting, combed yarn": {"name": "yarn spinning, ring, knitting, combed", "unit": "kg"},
        "Open end spinning": {"name": "yarn spinning, open-end", "unit": "kg"},
        "Open end spinning for weaving, carded yarn": {"name": "yarn spinning, open-end, weaving, carded", "unit": "kg"},
        "Open end spinning for knitting, carded yarn": {"name": "yarn spinning, open-end, knitting, carded", "unit": "kg"},
        "Air-jet spinning": {"name": "yarn spinning, air-jet", "unit": "kg"},
        "Air-jet spinning for knitting, carded yarn": {"name": "yarn spinning, air-jet, knitting, carded", "unit": "kg"},
        "Air-jet spinning for weaving, combed yarn": {"name": "yarn spinning, air-jet, weaving, combed", "unit": "kg"},
        "Vortex spinning": {"name": "yarn spinning, vortex", "unit": "kg"},
        "Vortex spinning for knitting, carded yarn": {"name": "yarn spinning, vortex, knitting, carded", "unit": "kg"},
        "Vortex spinning for weaving, combed yarn": {"name": "yarn spinning, vortex, weaving, combed", "unit": "kg"},
        "Multifilament spinning of synthetic yarns": {"name": "yarn spinning, multifilament, synthetic", "unit": "kg"},
        
        # Fabric construction - all variants from schema
        "Weaving": {"name": "weaving", "unit": "kg"},
        "Weaving - Air jet": {"name": "weaving, air-jet", "unit": "kg"},
        "Weaving - Water jet": {"name": "weaving, water-jet", "unit": "kg"},
        "Weaving - Rapier": {"name": "weaving, rapier", "unit": "kg"},
        "Weaving - Projectile": {"name": "weaving, projectile", "unit": "kg"},
        "Knitting - Circular": {"name": "knitting, circular", "unit": "kg"},
        "Knitting - Flatbed": {"name": "knitting, flat", "unit": "kg"},
        "Knitting - Warp": {"name": "knitting, warp", "unit": "kg"},
        "Non-woven": {"name": "nonwoven production", "unit": "kg"},
        "Non-woven, needle punch": {"name": "nonwoven production, needle punch", "unit": "kg"},
        "Non-woven, spunbond": {"name": "nonwoven production, spunbond", "unit": "kg"},
        
        # Dyeing and finishing - all variants from schema
        "Dyeing - Jet": {"name": "textile dyeing, jet", "unit": "kg"},
        "Jet dyeing - natural fibers / fiber blends": {"name": "textile dyeing, jet, natural fibers", "unit": "kg"},
        "Jet dyeing - synthetic fibers": {"name": "textile dyeing, jet, synthetic", "unit": "kg"},
        "Jigger dyeing": {"name": "textile dyeing, jigger", "unit": "kg"},
        "Pad batch dyeing": {"name": "textile dyeing, pad-batch", "unit": "kg"},
        "Pad-steam dyeing": {"name": "textile dyeing, pad-steam", "unit": "kg"},
        "Air-jet dyeing - natural fibers / fiber blends": {"name": "textile dyeing, air-jet, natural", "unit": "kg"},
        "No dyeing/printing": {"name": "no process", "unit": "kg"},
        "Spun-dyed (dope dyed)": {"name": "spun dyeing", "unit": "kg"},
        "Screen printing": {"name": "textile printing, screen", "unit": "kg"},
        "Digital printing": {"name": "textile printing, digital", "unit": "kg"},
        "Transfer printing": {"name": "textile printing, transfer", "unit": "kg"},
        "Finishing - Chemical": {"name": "textile finishing", "unit": "kg"},
        "Continuous - natural fibers / fiber blends": {"name": "textile finishing, continuous, natural", "unit": "kg"},
        "Continuous - synthetic fibers": {"name": "textile finishing, continuous, synthetic", "unit": "kg"},
        "Semi-continuous - natural fibers / fiber blends": {"name": "textile finishing, semi-continuous, natural", "unit": "kg"},
        "Semi-continuous - synthetic fibers": {"name": "textile finishing, semi-continuous, synthetic", "unit": "kg"},
        "Batch - natural fibers": {"name": "textile finishing, batch, natural", "unit": "kg"},
        "Batch - synthetic fibers": {"name": "textile finishing, batch, synthetic", "unit": "kg"},
        
        # Transport
        "Truck": {"name": "transport, freight, lorry", "unit": "tkm"},
        "Container ship": {"name": "transport, freight, sea, container ship", "unit": "tkm"},
        "Aircraft": {"name": "transport, freight, aircraft", "unit": "tkm"},
        "Train": {"name": "transport, freight, train", "unit": "tkm"},
        
        # End of life
        "Incineration": {"name": "waste textile incineration", "unit": "kg"},
        "Landfill": {"name": "waste textile landfill", "unit": "kg"},
        "Recycling": {"name": "textile recycling", "unit": "kg"},
        
        # Energy
        "Electricity": {"name": "electricity production", "unit": "kWh"},
        "Natural gas": {"name": "natural gas, burned", "unit": "MJ"},
        "Steam": {"name": "steam production", "unit": "MJ"},
        
        # Water and chemicals
        "Water": {"name": "tap water production", "unit": "kg"},
        "Wastewater treatment": {"name": "wastewater treatment", "unit": "m3"},
        
        # ============== FOOTWEAR ACTIVITIES ==============
        # Upper materials
        "Leather": {"name": "leather production", "unit": "kg"},
        "Synthetic leather": {"name": "synthetic leather production", "unit": "kg"},
        "Textile - woven": {"name": "textile woven production", "unit": "kg"},
        "Textile - knit": {"name": "textile knit production", "unit": "kg"},
        "Mesh": {"name": "mesh fabric production", "unit": "kg"},
        "Rubber": {"name": "rubber production", "unit": "kg"},
        "TPU": {"name": "TPU production", "unit": "kg"},
        "Recycled polyester": {"name": "recycled polyester production", "unit": "kg"},
        "Organic cotton": {"name": "organic cotton production", "unit": "kg"},
        
        # Sole materials
        "Rubber - natural": {"name": "natural rubber production", "unit": "kg"},
        "Rubber - synthetic": {"name": "synthetic rubber production", "unit": "kg"},
        "EVA": {"name": "EVA foam production", "unit": "kg"},
        "PU foam": {"name": "PU foam production", "unit": "kg"},
        "Cork": {"name": "cork production", "unit": "kg"},
        "Recycled rubber": {"name": "recycled rubber production", "unit": "kg"},
        
        # ============== CONSTRUCTION ACTIVITIES ==============
        # Main materials
        "Portland cement": {"name": "portland cement production", "unit": "kg"},
        "Recycled aggregate": {"name": "recycled aggregate production", "unit": "kg"},
        "Virgin aggregate": {"name": "virgin aggregate production", "unit": "kg"},
        "Steel": {"name": "steel production", "unit": "kg"},
        "Glass wool": {"name": "glass wool insulation production", "unit": "kg"},
        "Stone wool": {"name": "stone wool insulation production", "unit": "kg"},
        "EPS": {"name": "expanded polystyrene production", "unit": "kg"},
        "XPS": {"name": "extruded polystyrene production", "unit": "kg"},
        "PIR": {"name": "PIR insulation production", "unit": "kg"},
        "Wood fiber": {"name": "wood fiber insulation production", "unit": "kg"},
        "Timber - softwood": {"name": "softwood timber production", "unit": "kg"},
        "Timber - hardwood": {"name": "hardwood timber production", "unit": "kg"},
        "Clay brick": {"name": "clay brick production", "unit": "kg"},
        "Concrete block": {"name": "concrete block production", "unit": "kg"},
        "Concrete": {"name": "concrete production", "unit": "kg"},
        "Aluminum": {"name": "aluminum production", "unit": "kg"},
        "Glass": {"name": "flat glass production", "unit": "kg"},
        
        # Additives
        "Plasticizer": {"name": "plasticizer production", "unit": "kg"},
        "Accelerator": {"name": "concrete accelerator production", "unit": "kg"},
        "Retarder": {"name": "concrete retarder production", "unit": "kg"},
        "Air entrainer": {"name": "air entraining agent production", "unit": "kg"},
        "Water reducer": {"name": "water reducing agent production", "unit": "kg"},
        "Pigment": {"name": "pigment production", "unit": "kg"},
        "Fiber reinforcement": {"name": "fiber reinforcement production", "unit": "kg"},
        
        # ============== BATTERY ACTIVITIES ==============
        # Cathode materials
        "NMC (Nickel Manganese Cobalt)": {"name": "NMC cathode production", "unit": "kg"},
        "LFP (Lithium Iron Phosphate)": {"name": "LFP cathode production", "unit": "kg"},
        "NCA (Nickel Cobalt Aluminum)": {"name": "NCA cathode production", "unit": "kg"},
        "LMO (Lithium Manganese Oxide)": {"name": "LMO cathode production", "unit": "kg"},
        "nmc": {"name": "NMC cathode production", "unit": "kg"},
        "lfp": {"name": "LFP cathode production", "unit": "kg"},
        "nca": {"name": "NCA cathode production", "unit": "kg"},
        "lmo": {"name": "LMO cathode production", "unit": "kg"},
        
        # Anode materials
        "Graphite - natural": {"name": "natural graphite anode production", "unit": "kg"},
        "Graphite - synthetic": {"name": "synthetic graphite anode production", "unit": "kg"},
        "Silicon-graphite composite": {"name": "silicon-graphite anode production", "unit": "kg"},
        "Lithium metal": {"name": "lithium metal anode production", "unit": "kg"},
        "Lithium titanate": {"name": "lithium titanate anode production", "unit": "kg"},
        "graphite": {"name": "graphite anode production", "unit": "kg"},
        
        # Electrolyte
        "Liquid - LiPF6": {"name": "liquid electrolyte production", "unit": "kg"},
        "Solid - polymer": {"name": "solid polymer electrolyte production", "unit": "kg"},
        "Solid - ceramic": {"name": "solid ceramic electrolyte production", "unit": "kg"},
        "Gel": {"name": "gel electrolyte production", "unit": "kg"},
        "electrolyte": {"name": "electrolyte production", "unit": "kg"},
        
        # Separator
        "Polyethylene": {"name": "PE separator production", "unit": "kg"},
        "Polypropylene": {"name": "PP separator production", "unit": "kg"},
        "Ceramic coated": {"name": "ceramic coated separator production", "unit": "kg"},
        "Composite": {"name": "composite separator production", "unit": "kg"},
        
        # Housing
        "Cylindrical": {"name": "cylindrical cell housing production", "unit": "kg"},
        "Prismatic": {"name": "prismatic cell housing production", "unit": "kg"},
        "Pouch": {"name": "pouch cell housing production", "unit": "kg"},
    }

    def __init__(self, project_name: str = "EUFSI_LCA"):
        self.project_name = project_name
        self._initialized = False
    
    def _normalize_activity_code(self, name: str) -> str:
        """Normalize activity name to a valid code"""
        if not name:
            return ""
        # Remove commas, parentheses, and normalize spaces/dashes to underscores
        code = name.lower()
        code = code.replace(",", "").replace("(", "").replace(")", "")
        # Handle " - " specially to avoid double underscores
        code = code.replace(" - ", "_")
        code = code.replace(" ", "_")
        code = code.replace("-", "_")
        # Remove double underscores
        while "__" in code:
            code = code.replace("__", "_")
        return code.strip("_")
        
    def initialize(self):
        """Initialize Brightway2 project and databases"""
        if self._initialized:
            return
            
        # Set project directory
        os.environ['BRIGHTWAY2_DIR'] = str(BW_PROJECT_DIR)
        
        # Create or switch to project
        if self.project_name not in projects:
            projects.create_project(self.project_name, switch=True)
        else:
            projects.set_current(self.project_name)
        
        # Setup basic methods if not already done
        if not methods:
            bw2setup()
            
        self._initialized = True
        logger.info(f"Brightway2 initialized with project: {self.project_name}")
    
    def setup_database(self, db_name: str):
        """Setup LCA database for calculations"""
        self.initialize()
        
        # Always recreate database to ensure correct activity codes
        if db_name in databases:
            del databases[db_name]
        
        # Create a database with textile-specific activities
        new_db = Database(db_name)
        new_db.register()
        
        # Add textile activities based on mapping
        activities_data = {}
        for activity_key, activity_info in self.TEXTILE_ACTIVITY_MAPPING.items():
            act_code = self._normalize_activity_code(activity_key)
            activities_data[(db_name, act_code)] = {
                    'name': activity_info['name'],
                    'unit': activity_info['unit'],
                    'location': 'GLO',
                    'type': 'process',
                    'exchanges': [{
                        'input': (db_name, act_code),
                        'amount': 1.0,
                        'type': 'production',
                        'unit': activity_info['unit']
                    }]
                }
            
        new_db.write(activities_data)
        logger.info(f"Created database: {db_name} with {len(activities_data)} activities")
        
        return db_name
    
    def create_product_system(self, project: LCAProject, input_data: Dict) -> Dict:
        """Create a product system from input data for LCA calculation"""
        self.initialize()
        
        # Create a unique activity for this product
        product_db_name = f"product_{project.id}"
        
        if product_db_name in databases:
            del databases[product_db_name]
        
        product_db = Database(product_db_name)
        product_db.register()
        
        # Build exchanges based on input data
        exchanges = []
        weight_kg = project.product_weight_grams / 1000
        
        if project.industry == "textile" and input_data:
            exchanges = self._build_textile_exchanges(input_data, weight_kg, project)
        elif project.industry == "footwear":
            exchanges = self._build_footwear_exchanges(input_data, weight_kg, project)
        elif project.industry == "construction":
            exchanges = self._build_construction_exchanges(input_data, weight_kg, project)
        elif project.industry == "battery":
            exchanges = self._build_battery_exchanges(input_data, weight_kg, project)
        
        # Create the product activity
        product_activity = {
            (product_db_name, 'main_product'): {
                'name': project.name,
                'unit': 'unit',
                'location': 'GLO',
                'type': 'process',
                'exchanges': [
                    {
                        'input': (product_db_name, 'main_product'),
                        'amount': 1.0,
                        'type': 'production',
                        'unit': 'unit'
                    }
                ] + exchanges
            }
        }
        
        product_db.write(product_activity)
        
        return {
            'database': product_db_name,
            'activity_key': (product_db_name, 'main_product')
        }
    
    def _build_textile_exchanges(self, input_data: Dict, weight_kg: float, project: LCAProject) -> List[Dict]:
        """Build exchanges for textile products"""
        exchanges = []
        base_db = project.database
        
        # Fiber production impacts
        if 'yarns' in input_data:
            for yarn in input_data['yarns']:
                yarn_weight = weight_kg * (yarn.get('percentage', 0) / 100)
                if 'fibers' in yarn:
                    for fiber in yarn['fibers']:
                        fiber_weight = yarn_weight * (fiber.get('percentage', 0) / 100)
                        fiber_code = self._normalize_activity_code(fiber.get('material', ''))
                        exchanges.append({
                            'input': (base_db, fiber_code if fiber_code else 'cotton_fiber_global'),
                            'amount': fiber_weight,
                            'type': 'technosphere',
                            'unit': 'kg'
                        })
                
                # Spinning process
                spinning_method = yarn.get('spinning_method', 'Ring spinning')
                spinning_code = self._normalize_activity_code(spinning_method)
                exchanges.append({
                    'input': (base_db, spinning_code if spinning_code else 'ring_spinning'),
                    'amount': yarn_weight,
                    'type': 'technosphere',
                    'unit': 'kg'
                })
        
        # Fabric production
        if 'fabrics' in input_data:
            for fabric in input_data['fabrics']:
                fabric_weight = weight_kg * (fabric.get('percentage', 0) / 100)
                construction = fabric.get('construction_method', 'Weaving')
                construction_code = self._normalize_activity_code(construction)
                exchanges.append({
                    'input': (base_db, construction_code if construction_code else 'weaving'),
                    'amount': fabric_weight,
                    'type': 'technosphere',
                    'unit': 'kg'
                })
                
                # Dyeing
                coloring = fabric.get('coloring_method', '')
                if coloring and coloring != 'No dyeing/printing':
                    coloring_code = self._normalize_activity_code(coloring)
                    exchanges.append({
                        'input': (base_db, coloring_code if coloring_code else 'dyeing_jet'),
                        'amount': fabric_weight,
                        'type': 'technosphere',
                        'unit': 'kg'
                    })
        
        # Manufacturing waste
        if 'manufacturing' in input_data:
            mfg = input_data['manufacturing']
            waste_rate = mfg.get('cutting_waste_percentage', 0) / 100
            waste_amount = weight_kg * waste_rate
            
            # Distribute waste to end-of-life
            if waste_amount > 0:
                recycled = waste_amount * (mfg.get('waste_recycled_percentage', 0) / 100)
                incinerated = waste_amount * (mfg.get('waste_incinerated_percentage', 0) / 100)
                landfilled = waste_amount * (mfg.get('waste_landfilled_percentage', 0) / 100)
                
                if recycled > 0:
                    exchanges.append({
                        'input': (base_db, 'recycling'),
                        'amount': recycled,
                        'type': 'technosphere',
                        'unit': 'kg'
                    })
                if incinerated > 0:
                    exchanges.append({
                        'input': (base_db, 'incineration'),
                        'amount': incinerated,
                        'type': 'technosphere',
                        'unit': 'kg'
                    })
                if landfilled > 0:
                    exchanges.append({
                        'input': (base_db, 'landfill'),
                        'amount': landfilled,
                        'type': 'technosphere',
                        'unit': 'kg'
                    })
        
        # Transport
        if 'transport' in input_data:
            transport = input_data['transport']
            for leg in transport.get('legs', []):
                mode = leg.get('mode', 'Truck')
                distance = leg.get('distance_km', 0)
                tkm = weight_kg * distance / 1000  # tonne-kilometers
                mode_code = mode.lower().replace(" ", "_")
                exchanges.append({
                    'input': (base_db, mode_code if mode_code else 'truck'),
                    'amount': tkm,
                    'type': 'technosphere',
                    'unit': 'tkm'
                })
        
        # Use phase (if cradle-to-grave)
        if project.scope in ['cradle-to-grave', 'both'] and 'use_phase' in input_data:
            use = input_data['use_phase']
            if use.get('include', False):
                cycles = use.get('lifetime_washing_cycles', 0)
                # Water and energy per wash cycle
                water_per_cycle = 50  # liters
                energy_per_cycle = 0.5  # kWh
                
                exchanges.append({
                    'input': (base_db, 'water'),
                    'amount': cycles * water_per_cycle / 1000,  # m3
                    'type': 'technosphere',
                    'unit': 'kg'
                })
                exchanges.append({
                    'input': (base_db, 'electricity'),
                    'amount': cycles * energy_per_cycle,
                    'type': 'technosphere',
                    'unit': 'kWh'
                })
        
        # End of life (if cradle-to-grave)
        if project.scope in ['cradle-to-grave', 'both'] and 'end_of_life' in input_data:
            eol = input_data['end_of_life']
            if eol.get('include', False):
                recycled = weight_kg * (eol.get('recycled_percentage', 0) / 100)
                incinerated = weight_kg * (eol.get('incinerated_percentage', 0) / 100)
                landfilled = weight_kg * (eol.get('landfill_percentage', 0) / 100)
                
                if recycled > 0:
                    exchanges.append({
                        'input': (base_db, 'recycling'),
                        'amount': recycled,
                        'type': 'technosphere',
                        'unit': 'kg'
                    })
                if incinerated > 0:
                    exchanges.append({
                        'input': (base_db, 'incineration'),
                        'amount': incinerated,
                        'type': 'technosphere',
                        'unit': 'kg'
                    })
                if landfilled > 0:
                    exchanges.append({
                        'input': (base_db, 'landfill'),
                        'amount': landfilled,
                        'type': 'technosphere',
                        'unit': 'kg'
                    })
        
        return exchanges
    
    def _build_footwear_exchanges(self, input_data: Dict, weight_kg: float, project: LCAProject) -> List[Dict]:
        """Build exchanges for footwear products"""
        exchanges = []
        base_db = project.database
        
        # Upper materials
        if 'upper_materials' in input_data:
            for material in input_data['upper_materials']:
                mat_weight = weight_kg * (material.get('percentage', 0) / 100)
                mat_code = material.get('type', 'leather').lower().replace(" ", "_")
                exchanges.append({
                    'input': (base_db, mat_code),
                    'amount': mat_weight,
                    'type': 'technosphere',
                    'unit': 'kg'
                })
        
        # Sole materials
        if 'sole_materials' in input_data:
            for material in input_data['sole_materials']:
                mat_weight = weight_kg * (material.get('percentage', 0) / 100)
                mat_code = material.get('type', 'rubber').lower().replace(" ", "_")
                exchanges.append({
                    'input': (base_db, mat_code),
                    'amount': mat_weight,
                    'type': 'technosphere',
                    'unit': 'kg'
                })
        
        return exchanges
    
    def _build_construction_exchanges(self, input_data: Dict, weight_kg: float, project: LCAProject) -> List[Dict]:
        """Build exchanges for construction materials"""
        exchanges = []
        base_db = project.database
        
        # Main material
        if 'main_material' in input_data:
            mat = input_data['main_material']
            mat_code = mat.get('type', 'concrete').lower().replace(" ", "_")
            exchanges.append({
                'input': (base_db, mat_code),
                'amount': weight_kg,
                'type': 'technosphere',
                'unit': 'kg'
            })
        
        # Additives
        if 'additives' in input_data:
            for additive in input_data['additives']:
                add_weight = weight_kg * (additive.get('percentage', 0) / 100)
                add_code = additive.get('type', '').lower().replace(" ", "_")
                if add_code:
                    exchanges.append({
                        'input': (base_db, add_code),
                        'amount': add_weight,
                        'type': 'technosphere',
                        'unit': 'kg'
                    })
        
        return exchanges
    
    def _build_battery_exchanges(self, input_data: Dict, weight_kg: float, project: LCAProject) -> List[Dict]:
        """Build exchanges for battery systems"""
        exchanges = []
        base_db = project.database
        
        # Cathode material
        if 'cathode' in input_data:
            cathode = input_data['cathode']
            cat_weight = weight_kg * (cathode.get('percentage', 0) / 100)
            cat_code = cathode.get('chemistry', 'nmc').lower().replace(" ", "_")
            exchanges.append({
                'input': (base_db, cat_code),
                'amount': cat_weight,
                'type': 'technosphere',
                'unit': 'kg'
            })
        
        # Anode material
        if 'anode' in input_data:
            anode = input_data['anode']
            an_weight = weight_kg * (anode.get('percentage', 0) / 100)
            an_code = anode.get('material', 'graphite').lower().replace(" ", "_")
            exchanges.append({
                'input': (base_db, an_code),
                'amount': an_weight,
                'type': 'technosphere',
                'unit': 'kg'
            })
        
        # Electrolyte
        if 'electrolyte' in input_data:
            elec = input_data['electrolyte']
            elec_weight = weight_kg * (elec.get('percentage', 0) / 100)
            exchanges.append({
                'input': (base_db, 'electrolyte'),
                'amount': elec_weight,
                'type': 'technosphere',
                'unit': 'kg'
            })
        
        return exchanges
    
    def calculate_lca(self, project: LCAProject, input_data: Dict) -> Dict[str, Any]:
        """Perform real LCA calculation using Brightway2"""
        self.initialize()
        
        # Setup the database
        self.setup_database(project.database)
        
        # Create product system
        product_system = self.create_product_system(project, input_data)
        
        results = {
            'impact_categories': {},
            'contribution_by_stage': {},
            'total_impacts': {},
            'method': project.method
        }
        
        # Get impact categories for selected method
        method_categories = self.IMPACT_CATEGORIES.get(project.method, self.IMPACT_CATEGORIES['ReCiPe'])
        
        # Calculate impacts for each category
        for cat_key, cat_info in method_categories.items():
            try:
                # Find matching method in Brightway2
                method_tuple = self._find_method(cat_info[0], cat_info[1])
                
                if method_tuple:
                    # Get the activity
                    activity = Database(product_system['database']).get('main_product')
                    
                    # Perform LCA calculation
                    lca = bc.LCA({activity: 1}, method_tuple)
                    lca.lci()
                    lca.lcia()
                    
                    impact_value = float(lca.score)
                    
                    results['impact_categories'][cat_key] = {
                        'value': impact_value,
                        'unit': cat_info[3],
                        'abbreviation': cat_info[2],
                        'name': cat_info[1]
                    }
                    
                    # Contribution analysis by stage
                    results['contribution_by_stage'][cat_key] = self._calculate_contributions(
                        lca, input_data, project
                    )
                else:
                    # Use calculated estimates based on input data
                    estimated_value = self._estimate_impact(cat_key, input_data, project)
                    results['impact_categories'][cat_key] = {
                        'value': estimated_value,
                        'unit': cat_info[3],
                        'abbreviation': cat_info[2],
                        'name': cat_info[1]
                    }
                    results['contribution_by_stage'][cat_key] = self._estimate_contributions(
                        cat_key, input_data, project
                    )
                    
            except Exception as e:
                logger.warning(f"Error calculating {cat_key}: {str(e)}")
                # Fall back to estimation
                estimated_value = self._estimate_impact(cat_key, input_data, project)
                results['impact_categories'][cat_key] = {
                    'value': estimated_value,
                    'unit': cat_info[3],
                    'abbreviation': cat_info[2],
                    'name': cat_info[1]
                }
                results['contribution_by_stage'][cat_key] = self._estimate_contributions(
                    cat_key, input_data, project
                )
        
        # Calculate total weighted impact
        results['total_impacts'] = {
            'climate_change': results['impact_categories'].get('climate_change', {}).get('value', 0),
            'water_use': results['impact_categories'].get('water_depletion', results['impact_categories'].get('water_use', {})).get('value', 0),
        }
        
        return results
    
    def _find_method(self, method_family: str, category: str) -> Optional[tuple]:
        """Find a matching LCIA method in Brightway2"""
        for method in methods:
            method_name = ' '.join(method).lower()
            if method_family.lower() in method_name and category.lower() in method_name:
                return method
        return None

    def _calculate_contributions(self, lca: bc.LCA, input_data: Dict, project: LCAProject) -> Dict[str, float]:
        """
        Calculate contribution by life cycle stage based on real Brightway2 results.

        Uses the characterized inventory and a mapping from life-cycle stages
        to the activities that represent those stages.
        """
        # If no impact or something went wrong, fall back to simple equal split
        if lca.score is None:
            return {}

        characterized_inventory = lca.characterized_inventory
        activity_dict = lca.activity_dict  # maps (db_name, code) -> index

        # Build mapping of stages -> [(db_name, act_code), ...]
        stage_mapping = self._build_stage_mapping(project, input_data)

        contributions: Dict[str, float] = {}

        for stage, activities in stage_mapping.items():
            stage_score = 0.0
            for db_name, act_code in activities:
                key = (db_name, act_code)
                if key in activity_dict:
                    idx = activity_dict[key]
                    stage_score += float(characterized_inventory[idx])
            contributions[stage] = stage_score

        return contributions

    def _build_stage_mapping(self, project: LCAProject, input_data: Dict) -> Dict[str, List[tuple]]:
        """
        Map life-cycle stages to Brightway2 activity keys (database, activity_code).

        This reuses the same coding logic as the _build_*_exchanges methods,
        so stage contributions follow what was actually modeled.
        """
        base_db = project.database
        stages: Dict[str, List[tuple]] = {}

        if project.industry == "textile":
            stages = {
                "raw_materials": [],
                "yarn_production": [],
                "fabric_production": [],
                "dyeing_finishing": [],
                "manufacturing": [],
                "transport": [],
            }
            if project.scope in ["cradle-to-grave", "both"]:
                stages["use_phase"] = []
                stages["end_of_life"] = []

            # Raw materials & spinning
            for yarn in input_data.get("yarns", []):
                yarn_pct = yarn.get("percentage", 0)
                if "fibers" in yarn:
                    for fiber in yarn["fibers"]:
                        mat = fiber.get("material", "")
                        fiber_code = self._normalize_activity_code(mat)
                        if fiber_code:
                            stages["raw_materials"].append((base_db, fiber_code))

                spinning_method = yarn.get("spinning_method", "Ring spinning")
                spinning_code = self._normalize_activity_code(spinning_method)
                if spinning_code:
                    stages["yarn_production"].append((base_db, spinning_code))

            # Fabric + dyeing/printing
            for fabric in input_data.get("fabrics", []):
                construction = fabric.get("construction_method", "Weaving")
                construction_code = self._normalize_activity_code(construction)
                if construction_code:
                    stages["fabric_production"].append((base_db, construction_code))

                coloring = fabric.get("coloring_method", "")
                if coloring and coloring != "No dyeing/printing":
                    coloring_code = self._normalize_activity_code(coloring)
                    if coloring_code:
                        stages["dyeing_finishing"].append((base_db, coloring_code))

            # Manufacturing waste (recycling/incineration/landfill)
            if "manufacturing" in input_data:
                mfg = input_data["manufacturing"]
                # The exchanges use literal codes 'recycling', 'incineration', 'landfill'
                if mfg.get("waste_recycled_percentage", 0) > 0:
                    stages.setdefault("manufacturing", []).append((base_db, "recycling"))
                if mfg.get("waste_incinerated_percentage", 0) > 0:
                    stages.setdefault("manufacturing", []).append((base_db, "incineration"))
                if mfg.get("waste_landfilled_percentage", 0) > 0:
                    stages.setdefault("manufacturing", []).append((base_db, "landfill"))

            # Transport
            transport = input_data.get("transport", {})
            for leg in transport.get("legs", []):
                mode = leg.get("mode", "Truck")
                mode_code = mode.lower().replace(" ", "_")
                stages["transport"].append((base_db, mode_code))

            # Use phase
            if project.scope in ["cradle-to-grave", "both"]:
                use = input_data.get("use_phase", {})
                if use.get("include", False):
                    # In exchanges: 'water' and 'electricity'
                    stages["use_phase"].append((base_db, "water"))
                    stages["use_phase"].append((base_db, "electricity"))

            # End of life
            if project.scope in ["cradle-to-grave", "both"]:
                eol = input_data.get("end_of_life", {})
                if eol.get("recycled_percentage", 0) > 0:
                    stages["end_of_life"].append((base_db, "recycling"))
                if eol.get("incinerated_percentage", 0) > 0:
                    stages["end_of_life"].append((base_db, "incineration"))
                if eol.get("landfill_percentage", 0) > 0:
                    stages["end_of_life"].append((base_db, "landfill"))

        elif project.industry == "footwear":
            stages = {
                "raw_materials": [],
                "component_production": [],
                "assembly": [],
                "transport": [],
            }
            if project.scope in ["cradle-to-grave", "both"]:
                stages["use_phase"] = []
                stages["end_of_life"] = []

            for mat in input_data.get("upper_materials", []):
                mat_code = mat.get("type", "").lower().replace(" ", "_")
                if mat_code:
                    stages["raw_materials"].append((base_db, mat_code))
            for mat in input_data.get("sole_materials", []):
                mat_code = mat.get("type", "").lower().replace(" ", "_")
                if mat_code:
                    stages["component_production"].append((base_db, mat_code))

            # You can extend with manufacturing, transport, etc., similar to textile.

        elif project.industry == "construction":
            stages = {
                "raw_materials": [],
                "processing": [],
                "transport": [],
                "installation": [],
            }
            if project.scope in ["cradle-to-grave", "both"]:
                stages["use_phase"] = []
                stages["end_of_life"] = []

            main = input_data.get("main_material", {})
            mat_code = main.get("type", "").lower().replace(" ", "_")
            if mat_code:
                stages["raw_materials"].append((base_db, mat_code))

            # Transport etc. can be wired similarly.

        else:  # battery
            stages = {
                "raw_materials": [],
                "cell_production": [],
                "pack_assembly": [],
                "transport": [],
            }
            if project.scope in ["cradle-to-grave", "both"]:
                stages["use_phase"] = []
                stages["end_of_life"] = []

            cathode = input_data.get("cathode", {})
            cat_code = cathode.get("chemistry", "nmc").lower().replace(" ", "_")
            stages["raw_materials"].append((base_db, cat_code))

            anode = input_data.get("anode", {})
            an_code = anode.get("material", "graphite").lower().replace(" ", "_")
            stages["raw_materials"].append((base_db, an_code))

            electrolyte = input_data.get("electrolyte", {})
            if electrolyte:
                stages["raw_materials"].append((base_db, "electrolyte"))

        # Remove empty stages to avoid clutter
        return {k: v for k, v in stages.items() if v}
    
    def trace_impact_origin(self, project: LCAProject, input_data: Dict, impact_category: str, life_cycle_stage: str) -> Dict[str, Any]:
        """
        Trace the origin of an impact result for a specific category and life cycle stage.
        Shows which activities, exchanges, and characterization factors contribute to it.
        """
        weight_kg = project.product_weight_grams / 1000
        
        # Define characterization factors for different impact categories
        # These are based on standard LCA methodology (simplified for demonstration)
        characterization_factors = {
            'climate_change': {
                'CO2': {'factor': 1.0, 'unit': 'kg CO2-eq/kg CO2'},
                'CH4': {'factor': 28.0, 'unit': 'kg CO2-eq/kg CH4'},
                'N2O': {'factor': 265.0, 'unit': 'kg CO2-eq/kg N2O'},
                'SF6': {'factor': 23500.0, 'unit': 'kg CO2-eq/kg SF6'},
                'HFC-134a': {'factor': 1300.0, 'unit': 'kg CO2-eq/kg HFC'},
            },
            'water_depletion': {
                'freshwater': {'factor': 1.0, 'unit': 'm3/m3'},
                'groundwater': {'factor': 1.2, 'unit': 'm3/m3'},
                'surface_water': {'factor': 0.8, 'unit': 'm3/m3'},
            },
            'terrestrial_acidification': {
                'SO2': {'factor': 1.0, 'unit': 'kg SO2-eq/kg SO2'},
                'NOx': {'factor': 0.5, 'unit': 'kg SO2-eq/kg NOx'},
                'NH3': {'factor': 1.6, 'unit': 'kg SO2-eq/kg NH3'},
            },
            'freshwater_eutrophication': {
                'PO4': {'factor': 1.0, 'unit': 'kg P-eq/kg PO4'},
                'P': {'factor': 3.06, 'unit': 'kg P-eq/kg P'},
            },
            'human_toxicity': {
                'benzene': {'factor': 1.9e-3, 'unit': 'CTUh/kg'},
                'formaldehyde': {'factor': 2.1e-6, 'unit': 'CTUh/kg'},
                'lead': {'factor': 4.5e-5, 'unit': 'CTUh/kg'},
            },
        }
        
        # Map life cycle stages to activities
        stage_activity_mapping = {
            'textile': {
                'raw_materials': ['fiber_production', 'fiber_processing'],
                'yarn_production': ['spinning', 'yarn_twisting', 'yarn_winding'],
                'fabric_production': ['weaving', 'knitting', 'finishing_prep'],
                'dyeing_finishing': ['dyeing', 'printing', 'finishing'],
                'manufacturing': ['cutting', 'sewing', 'assembly'],
                'transport': ['road_transport', 'sea_transport', 'air_transport'],
                'use_phase': ['washing', 'drying', 'ironing'],
                'end_of_life': ['recycling', 'incineration', 'landfill'],
            },
            'footwear': {
                'raw_materials': ['leather_production', 'rubber_production', 'textile_production'],
                'component_production': ['sole_manufacturing', 'upper_production'],
                'assembly': ['lasting', 'cementing', 'finishing'],
                'transport': ['road_transport', 'sea_transport'],
                'use_phase': ['cleaning', 'maintenance'],
                'end_of_life': ['recycling', 'incineration', 'landfill'],
            },
            'construction': {
                'raw_materials': ['cement_production', 'aggregate_extraction', 'steel_production'],
                'processing': ['mixing', 'forming', 'curing'],
                'transport': ['road_transport', 'rail_transport'],
                'installation': ['site_work', 'installation', 'finishing'],
                'use_phase': ['maintenance', 'repair'],
                'end_of_life': ['demolition', 'recycling', 'landfill'],
            },
            'battery': {
                'raw_materials': ['lithium_extraction', 'cobalt_mining', 'nickel_production'],
                'cell_production': ['electrode_coating', 'cell_assembly', 'formation'],
                'pack_assembly': ['module_assembly', 'bms_integration', 'pack_finishing'],
                'transport': ['road_transport', 'sea_transport'],
                'use_phase': ['charging_losses', 'thermal_management'],
                'end_of_life': ['disassembly', 'recycling', 'disposal'],
            }
        }
        
        # Define emission factors per activity (kg emission / kg product)
        activity_emissions = {
            # Textile - Yarn Production
            'spinning': {
                'CO2': 0.45, 'CH4': 0.002, 'SO2': 0.001, 'NOx': 0.002,
                'electricity_kwh': 2.5, 'steam_mj': 5.0
            },
            'yarn_twisting': {
                'CO2': 0.15, 'CH4': 0.001, 'SO2': 0.0005, 'NOx': 0.001,
                'electricity_kwh': 1.2
            },
            'yarn_winding': {
                'CO2': 0.08, 'CH4': 0.0005, 'electricity_kwh': 0.8
            },
            # Textile - Raw Materials
            'fiber_production': {
                'CO2': 3.5, 'CH4': 0.05, 'N2O': 0.02, 'SO2': 0.01, 'NOx': 0.02,
                'freshwater': 50.0, 'PO4': 0.005, 'P': 0.001
            },
            'fiber_processing': {
                'CO2': 0.8, 'CH4': 0.01, 'SO2': 0.005, 'electricity_kwh': 3.0
            },
            # Textile - Fabric Production
            'weaving': {
                'CO2': 0.6, 'CH4': 0.003, 'electricity_kwh': 4.0
            },
            'knitting': {
                'CO2': 0.4, 'CH4': 0.002, 'electricity_kwh': 2.8
            },
            'finishing_prep': {
                'CO2': 0.3, 'CH4': 0.001, 'freshwater': 20.0
            },
            # Textile - Dyeing & Finishing
            'dyeing': {
                'CO2': 1.2, 'CH4': 0.01, 'SO2': 0.008, 'NOx': 0.005,
                'freshwater': 100.0, 'steam_mj': 15.0, 'benzene': 0.00001
            },
            'printing': {
                'CO2': 0.5, 'CH4': 0.003, 'freshwater': 30.0
            },
            'finishing': {
                'CO2': 0.8, 'CH4': 0.005, 'formaldehyde': 0.0001
            },
            # Textile - Manufacturing
            'cutting': {
                'CO2': 0.1, 'electricity_kwh': 0.5
            },
            'sewing': {
                'CO2': 0.15, 'electricity_kwh': 0.8
            },
            'assembly': {
                'CO2': 0.08, 'electricity_kwh': 0.3
            },
            # Transport
            'road_transport': {
                'CO2': 0.1, 'CH4': 0.0001, 'NOx': 0.001, 'SO2': 0.0002
            },
            'sea_transport': {
                'CO2': 0.02, 'CH4': 0.00002, 'NOx': 0.0004, 'SO2': 0.0003
            },
            'air_transport': {
                'CO2': 1.2, 'CH4': 0.0003, 'NOx': 0.003
            },
            'rail_transport': {
                'CO2': 0.03, 'CH4': 0.00003, 'NOx': 0.0002
            },
            # Use phase
            'washing': {
                'CO2': 0.3, 'freshwater': 50.0, 'PO4': 0.001, 'electricity_kwh': 0.5
            },
            'drying': {
                'CO2': 0.5, 'CH4': 0.002, 'electricity_kwh': 2.5
            },
            'ironing': {
                'CO2': 0.2, 'electricity_kwh': 1.0
            },
            # End of life
            'recycling': {
                'CO2': -0.5, 'CH4': 0.01
            },
            'incineration': {
                'CO2': 2.0, 'CH4': 0.001, 'SO2': 0.005, 'NOx': 0.003
            },
            'landfill': {
                'CO2': 0.1, 'CH4': 0.2
            },
        }
        
        # Get activities for this stage
        industry_stages = stage_activity_mapping.get(project.industry, stage_activity_mapping['textile'])
        stage_activities = industry_stages.get(life_cycle_stage, [])
        
        # Get relevant characterization factors for this impact category
        cf_category = characterization_factors.get(impact_category, characterization_factors.get('climate_change', {}))
        
        # Build the trace result
        trace_result = {
            'impact_category': impact_category,
            'life_cycle_stage': life_cycle_stage,
            'product_weight_kg': weight_kg,
            'activities': [],
            'total_stage_impact': 0,
            'calculation_method': project.method,
            'database': project.database,
        }
        
        total_impact = 0
        
        for activity in stage_activities:
            activity_data = activity_emissions.get(activity, {})
            activity_trace = {
                'activity_name': activity.replace('_', ' ').title(),
                'activity_code': activity,
                'exchanges': [],
                'subtotal_impact': 0
            }
            
            activity_impact = 0
            
            # Calculate impact from each exchange (emission)
            for emission, emission_amount in activity_data.items():
                # Skip non-emission fields
                if emission in ['electricity_kwh', 'steam_mj']:
                    # Convert energy to CO2 emissions
                    if emission == 'electricity_kwh':
                        co2_factor = 0.5  # kg CO2/kWh (grid average)
                        emission_value = emission_amount * weight_kg * co2_factor
                        if 'CO2' in cf_category:
                            cf = cf_category['CO2']
                            impact_contribution = emission_value * cf['factor']
                            activity_trace['exchanges'].append({
                                'flow_name': f'Electricity consumption',
                                'flow_amount': emission_amount * weight_kg,
                                'flow_unit': 'kWh',
                                'emission_name': 'CO2 (from electricity)',
                                'emission_amount': round(emission_value, 6),
                                'emission_unit': 'kg',
                                'characterization_factor': cf['factor'],
                                'cf_unit': cf['unit'],
                                'impact_contribution': round(impact_contribution, 6),
                            })
                            activity_impact += impact_contribution
                    continue
                
                # Check if this emission contributes to the selected impact category
                if emission in cf_category:
                    cf = cf_category[emission]
                    emission_value = emission_amount * weight_kg
                    impact_contribution = emission_value * cf['factor']
                    
                    activity_trace['exchanges'].append({
                        'flow_name': f'{emission.upper()} emission',
                        'flow_amount': round(emission_value, 6),
                        'flow_unit': 'kg' if emission not in ['freshwater', 'groundwater', 'surface_water'] else 'm3',
                        'emission_name': emission.upper(),
                        'emission_amount': round(emission_value, 6),
                        'emission_unit': 'kg' if emission not in ['freshwater', 'groundwater', 'surface_water'] else 'm3',
                        'characterization_factor': cf['factor'],
                        'cf_unit': cf['unit'],
                        'impact_contribution': round(impact_contribution, 6),
                    })
                    activity_impact += impact_contribution
            
            activity_trace['subtotal_impact'] = round(activity_impact, 6)
            if activity_trace['exchanges']:  # Only add if there are relevant exchanges
                trace_result['activities'].append(activity_trace)
            total_impact += activity_impact
        
        trace_result['total_stage_impact'] = round(total_impact, 6)
        
        # Add summary statistics
        trace_result['summary'] = {
            'num_activities': len(trace_result['activities']),
            'num_exchanges': sum(len(a['exchanges']) for a in trace_result['activities']),
            'dominant_activity': max(trace_result['activities'], key=lambda x: x['subtotal_impact'])['activity_name'] if trace_result['activities'] else 'N/A',
            'unit': self._get_impact_unit(impact_category, project.method),
        }
        
        # Add methodology explanation
        trace_result['methodology'] = {
            'description': f"Impact calculated using {project.method} methodology with {project.database} database",
            'formula': "Impact = Σ (Activity Amount × Emission Factor × Characterization Factor)",
            'characterization_factors_used': [
                {'emission': k, 'factor': v['factor'], 'unit': v['unit']} 
                for k, v in cf_category.items()
            ]
        }
        
        return trace_result
    
    def _get_impact_unit(self, category: str, method: str) -> str:
        """Get the unit for an impact category"""
        method_cats = self.IMPACT_CATEGORIES.get(method, self.IMPACT_CATEGORIES['ReCiPe'])
        if category in method_cats:
            return method_cats[category][3]
        return 'unit'

    def _estimate_impact(self, category: str, input_data: Dict, project: LCAProject) -> float:
        """Estimate impact value based on input data using emission factors"""
        weight_kg = project.product_weight_grams / 1000
        
        # Base emission factors (kg CO2-eq per kg material)
        emission_factors = {
            'cotton': 5.9,
            'polyester': 9.5,
            'polyester_recycled': 2.1,
            'wool': 28.0,
            'viscose': 8.0,
            'lyocell': 3.5,
            'modal': 4.0,
            'nylon': 12.0,
            'elastane': 15.0,
            'acrylic': 11.0,
            'linen': 3.0,
            'hemp': 2.5,
            'silk': 100.0,
            'leather': 17.0,
            'rubber': 3.0,
            'concrete': 0.1,
            'steel': 2.0,
            'aluminum': 8.0,
            'lithium': 15.0,
            'cobalt': 30.0,
            'graphite': 3.0,
        }
        
        # Category-specific multipliers
        category_multipliers = {
            'climate_change': 1.0,
            'ozone_depletion': 0.000001,
            'terrestrial_acidification': 0.01,
            'acidification': 0.01,
            'freshwater_eutrophication': 0.001,
            'marine_eutrophication': 0.005,
            'human_toxicity': 0.1,
            'human_toxicity_cancer': 0.00001,
            'human_toxicity_non_cancer': 0.0001,
            'photochemical_oxidant_formation': 0.005,
            'photochemical_ozone_formation': 0.005,
            'particulate_matter': 0.001,
            'particulate_matter_formation': 0.001,
            'terrestrial_ecotoxicity': 0.01,
            'freshwater_ecotoxicity': 0.05,
            'ecotoxicity_freshwater': 0.05,
            'marine_ecotoxicity': 0.03,
            'ionising_radiation': 0.1,
            'agricultural_land_occupation': 5.0,
            'urban_land_occupation': 0.5,
            'natural_land_transformation': 0.01,
            'land_use': 10.0,
            'water_depletion': 50.0,
            'water_use': 50.0,
            'metal_depletion': 0.1,
            'resource_use_minerals': 0.0001,
            'fossil_depletion': 2.0,
            'resource_use_fossils': 20.0,
            'eutrophication_terrestrial': 0.02,
            'eutrophication_freshwater': 0.001,
            'eutrophication_marine': 0.005,
        }
        
        multiplier = category_multipliers.get(category, 1.0)
        
        # Calculate weighted emission factor based on composition
        total_ef = 0
        has_valid_input = False
        
        if project.industry == "textile" and input_data:
            if 'yarns' in input_data and input_data['yarns']:
                for yarn in input_data['yarns']:
                    yarn_pct = yarn.get('percentage', 0) / 100
                    # If yarn has no percentage, assume 100% for single yarn
                    if yarn_pct == 0 and len(input_data['yarns']) == 1:
                        yarn_pct = 1.0
                    fibers = yarn.get('fibers', [])
                    if fibers:
                        for fiber in fibers:
                            fiber_pct = fiber.get('percentage', 0) / 100
                            # If fiber has no percentage, assume 100% for single fiber
                            if fiber_pct == 0 and len(fibers) == 1:
                                fiber_pct = 1.0
                            fiber_material = fiber.get('material', 'cotton').lower().split()[0]
                            ef = emission_factors.get(fiber_material, 5.0)
                            total_ef += weight_kg * yarn_pct * fiber_pct * ef
                            if fiber_pct > 0:
                                has_valid_input = True
                    else:
                        # No fibers specified, use default cotton
                        total_ef += weight_kg * yarn_pct * 5.9  # Cotton default
                        if yarn_pct > 0:
                            has_valid_input = True
        
        # If no valid input data, use default estimation based on product weight
        if not has_valid_input or total_ef == 0:
            # Default: assume cotton t-shirt (5.9 kg CO2-eq/kg)
            total_ef = weight_kg * 5.9
        
        # Add process emissions
        process_factor = 1.5  # Additional 50% for processing
        transport_factor = 1.1  # Additional 10% for transport
        
        total_impact = total_ef * process_factor * transport_factor * multiplier
        
        # Add use phase if applicable
        if project.scope in ['cradle-to-grave', 'both'] and input_data:
            use_phase = input_data.get('use_phase', {})
            if use_phase.get('include', False):
                cycles = use_phase.get('lifetime_washing_cycles', 50)
                use_impact = cycles * 0.5 * multiplier  # 0.5 kg CO2-eq per wash cycle
                total_impact += use_impact
        
        return round(total_impact, 6)
    
    def _estimate_contributions(self, category: str, input_data: Dict, project: LCAProject) -> Dict[str, float]:
        """Estimate contribution by stage"""
        total = self._estimate_impact(category, input_data, project)
        
        if project.industry == "textile":
            base_contributions = {
                'raw_materials': 0.35,
                'yarn_production': 0.10,
                'fabric_production': 0.15,
                'dyeing_finishing': 0.15,
                'manufacturing': 0.05,
                'transport': 0.05,
            }
        elif project.industry == "footwear":
            base_contributions = {
                'raw_materials': 0.40,
                'component_production': 0.20,
                'assembly': 0.10,
                'transport': 0.10,
            }
        elif project.industry == "construction":
            base_contributions = {
                'raw_materials': 0.50,
                'processing': 0.20,
                'transport': 0.15,
                'installation': 0.10,
            }
        else:  # battery
            base_contributions = {
                'raw_materials': 0.45,
                'cell_production': 0.25,
                'pack_assembly': 0.10,
                'transport': 0.05,
            }
        
        if project.scope in ['cradle-to-grave', 'both']:
            base_contributions['use_phase'] = 0.10
            base_contributions['end_of_life'] = 0.05
        
        # Normalize to sum to 1
        total_pct = sum(base_contributions.values())
        
        return {k: round((v / total_pct) * total, 6) for k, v in base_contributions.items()}


# Initialize Brightway2 engine
bw_engine = Brightway2Engine()

# ============== INDUSTRY SCHEMAS ==============

TEXTILE_SCHEMA = {
    "industry": "textile",
    "name": "Textile LCA Input Schema",
    "description": "Comprehensive input schema for textile product LCA based on bAwear model",
    "sections": [
        {
            "id": "product",
            "title": "Product Information",
            "fields": [
                {"id": "product_id", "label": "Product ID", "type": "text", "required": True},
                {"id": "description", "label": "Description", "type": "textarea", "required": False},
                {"id": "weight_grams", "label": "Weight", "type": "number", "unit": "grams", "required": True},
                {"id": "product_scenario", "label": "Product Scenario", "type": "select", "required": True,
                 "options": [
                     "Activewear - Tee cotton", "Activewear - Tee polyester", "Activewear - Leggings",
                     "Casual - T-shirt cotton", "Casual - T-shirt blended", "Casual - Polo shirt",
                     "Casual - Jeans", "Casual - Chinos", "Casual - Dress",
                     "Formal - Shirt cotton", "Formal - Blouse", "Formal - Suit jacket",
                     "Outerwear - Jacket light", "Outerwear - Jacket winter", "Outerwear - Coat",
                     "Underwear - Briefs", "Underwear - Bra", "Underwear - Socks",
                     "Workwear - Work jacket", "Workwear - Work pants", "Workwear - Coverall"
                 ]}
            ]
        },
        {
            "id": "fibers",
            "title": "Fiber Composition",
            "repeatable": True,
            "max_items": 5,
            "fields": [
                {"id": "material", "label": "Fiber Material", "type": "select", "required": True,
                 "options": [
                     "Cotton fiber (Global)", "Cotton, organic (Global)", "Cotton, recycled (Global)",
                     "Polyester fiber (Global)", "Polyester, recycled (Global)",
                     "Wool fiber (Global)", "Wool, recycled (Global)",
                     "Viscose fiber (Global)", "Lyocell fiber (Global)", "Modal fiber (Global)",
                     "Elastane fiber (Global)", "Nylon fiber (Global)", "Nylon, recycled (Global)",
                     "Acrylic fiber (Global)", "Linen fiber (Global)", "Hemp fiber (Global)",
                     "Silk fiber (Global)", "Bamboo fiber (Global)"
                 ]},
                {"id": "percentage", "label": "Percentage", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True},
                {"id": "production_location", "label": "Production Location", "type": "select", "required": True,
                 "options": ["Global", "China", "India", "Bangladesh", "Vietnam", "Turkey", "Indonesia", 
                            "Pakistan", "USA", "Europe", "Brazil", "Egypt", "Thailand"]}
            ]
        },
        {
            "id": "yarns",
            "title": "Yarn Production",
            "repeatable": True,
            "max_items": 5,
            "fields": [
                {"id": "name", "label": "Yarn Name", "type": "text", "required": True},
                {"id": "count_nm", "label": "Yarn Count", "type": "number", "unit": "Nm", "required": True},
                {"id": "percentage", "label": "Percentage in Product", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True},
                {"id": "spinning_method", "label": "Spinning Method", "type": "select", "required": True,
                 "options": [
                     "Ring spinning for weaving, carded yarn", "Ring spinning for weaving, combed yarn",
                     "Ring spinning for knitting, carded yarn", "Ring spinning for knitting, combed yarn",
                     "Open end spinning for weaving, carded yarn", "Open end spinning for knitting, carded yarn",
                     "Air-jet spinning for knitting, carded yarn", "Air-jet spinning for weaving, combed yarn",
                     "Vortex spinning for knitting, carded yarn", "Vortex spinning for weaving, combed yarn",
                     "Multifilament spinning of synthetic yarns"
                 ]}
            ]
        },
        {
            "id": "fabrics",
            "title": "Fabric Production",
            "repeatable": True,
            "max_items": 3,
            "fields": [
                {"id": "name", "label": "Fabric Name", "type": "text", "required": True},
                {"id": "construction_method", "label": "Construction Method", "type": "select", "required": True,
                 "options": [
                     "Knitting - Circular", "Knitting - Flatbed", "Knitting - Warp",
                     "Weaving - Air jet", "Weaving - Water jet", "Weaving - Rapier",
                     "Weaving - Projectile", "Non-woven, needle punch", "Non-woven, spunbond"
                 ]},
                {"id": "percentage", "label": "Percentage in Product", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True},
                {"id": "finishing_method", "label": "Finishing Method", "type": "select", "required": True,
                 "options": [
                     "Continuous - natural fibers / fiber blends",
                     "Continuous - synthetic fibers",
                     "Semi-continuous - natural fibers / fiber blends",
                     "Semi-continuous - synthetic fibers",
                     "Batch - natural fibers", "Batch - synthetic fibers"
                 ]},
                {"id": "coloring_method", "label": "Coloring Method", "type": "select", "required": True,
                 "options": [
                     "No dyeing/printing", "Spun-dyed (dope dyed)",
                     "Jet dyeing - natural fibers / fiber blends", "Jet dyeing - synthetic fibers",
                     "Jigger dyeing", "Pad batch dyeing", "Pad-steam dyeing",
                     "Screen printing", "Digital printing", "Transfer printing"
                 ]},
                {"id": "color_depth", "label": "Color Depth", "type": "select", "required": True,
                 "options": ["Pale/Light", "Medium", "Dark", "Very Dark"]}
            ]
        },
        {
            "id": "manufacturing",
            "title": "Manufacturing",
            "fields": [
                {"id": "finish_treatment_1", "label": "Finish Treatment 1", "type": "select", "required": False,
                 "options": ["None", "Embroidery", "Ozone treatment", "Garment dyeing", "Ironing", 
                            "Stone wash", "Enzyme wash", "Laser finishing", "Transfer print"]},
                {"id": "finish_treatment_2", "label": "Finish Treatment 2", "type": "select", "required": False,
                 "options": ["None", "Embroidery", "Ozone treatment", "Garment dyeing", "Ironing",
                            "Stone wash", "Enzyme wash", "Laser finishing", "Transfer print"]},
                {"id": "cutting_waste_percentage", "label": "Cutting Waste", "type": "number", "unit": "%", "min": 0, "max": 50, "required": True},
                {"id": "waste_recycled_percentage", "label": "Waste Recycled", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True},
                {"id": "waste_incinerated_percentage", "label": "Waste Incinerated", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True},
                {"id": "waste_landfilled_percentage", "label": "Waste Landfilled", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True}
            ]
        },
        {
            "id": "production_locations",
            "title": "Production Locations & Energy",
            "fields": [
                {"id": "spinning_location", "label": "Spinning Location", "type": "select", "required": True,
                 "options": ["Global", "China", "India", "Bangladesh", "Vietnam", "Turkey", "Indonesia", 
                            "Pakistan", "USA", "Europe", "Brazil", "Egypt", "Thailand"]},
                {"id": "spinning_renewable_energy", "label": "Spinning Renewable Energy", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True},
                {"id": "fabric_construction_location", "label": "Fabric Construction Location", "type": "select", "required": True,
                 "options": ["Global", "China", "India", "Bangladesh", "Vietnam", "Turkey", "Indonesia", 
                            "Pakistan", "USA", "Europe", "Brazil", "Egypt", "Thailand"]},
                {"id": "fabric_construction_renewable_energy", "label": "Fabric Construction Renewable Energy", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True},
                {"id": "finishing_location", "label": "Finishing Location", "type": "select", "required": True,
                 "options": ["Global", "China", "India", "Bangladesh", "Vietnam", "Turkey", "Indonesia", 
                            "Pakistan", "USA", "Europe", "Brazil", "Egypt", "Thailand"]},
                {"id": "finishing_renewable_energy", "label": "Finishing Renewable Energy", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True},
                {"id": "manufacturing_location", "label": "Manufacturing Location", "type": "select", "required": True,
                 "options": ["Global", "China", "India", "Bangladesh", "Vietnam", "Turkey", "Indonesia", 
                            "Pakistan", "USA", "Europe", "Brazil", "Egypt", "Thailand"]},
                {"id": "manufacturing_renewable_energy", "label": "Manufacturing Renewable Energy", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True}
            ]
        },
        {
            "id": "transport",
            "title": "Transportation",
            "fields": [
                {"id": "final_destination", "label": "Final Destination", "type": "select", "required": True,
                 "options": ["Global", "Europe", "North America", "Asia", "South America", "Africa", "Oceania"]},
                {"id": "transport_1_mode", "label": "Transport 1 Mode", "type": "select", "required": True,
                 "options": ["Truck", "Container ship", "Aircraft", "Train", "Barge"]},
                {"id": "transport_1_distance", "label": "Transport 1 Distance", "type": "number", "unit": "km", "required": True},
                {"id": "transport_2_mode", "label": "Transport 2 Mode", "type": "select", "required": False,
                 "options": ["None", "Truck", "Container ship", "Aircraft", "Train", "Barge"]},
                {"id": "transport_2_distance", "label": "Transport 2 Distance", "type": "number", "unit": "km", "required": False},
                {"id": "transport_3_mode", "label": "Transport 3 Mode", "type": "select", "required": False,
                 "options": ["None", "Truck", "Container ship", "Aircraft", "Train", "Barge"]},
                {"id": "transport_3_distance", "label": "Transport 3 Distance", "type": "number", "unit": "km", "required": False}
            ]
        },
        {
            "id": "use_phase",
            "title": "Use Phase",
            "fields": [
                {"id": "include", "label": "Include Use Phase", "type": "boolean", "required": True},
                {"id": "washing_temperature", "label": "Washing Temperature", "type": "number", "unit": "°C", "required": False},
                {"id": "drying_method", "label": "Drying Method", "type": "select", "required": False,
                 "options": ["Line dry", "Tumble dry - low", "Tumble dry - medium", "Tumble dry - high"]},
                {"id": "ironing", "label": "Ironing", "type": "boolean", "required": False},
                {"id": "lifetime_washing_cycles", "label": "Lifetime Washing Cycles", "type": "number", "required": False}
            ]
        },
        {
            "id": "end_of_life",
            "title": "End of Life",
            "fields": [
                {"id": "include", "label": "Include End of Life", "type": "boolean", "required": True},
                {"id": "recycled_percentage", "label": "Recycled", "type": "number", "unit": "%", "min": 0, "max": 100, "required": False},
                {"id": "incinerated_percentage", "label": "Incinerated", "type": "number", "unit": "%", "min": 0, "max": 100, "required": False},
                {"id": "landfill_percentage", "label": "Landfill", "type": "number", "unit": "%", "min": 0, "max": 100, "required": False}
            ]
        }
    ]
}

FOOTWEAR_SCHEMA = {
    "industry": "footwear",
    "name": "Footwear LCA Input Schema",
    "description": "Input schema for footwear product LCA",
    "sections": [
        {
            "id": "product",
            "title": "Product Information",
            "fields": [
                {"id": "product_id", "label": "Product ID", "type": "text", "required": True},
                {"id": "description", "label": "Description", "type": "textarea", "required": False},
                {"id": "weight_grams", "label": "Weight (per pair)", "type": "number", "unit": "grams", "required": True},
                {"id": "product_type", "label": "Product Type", "type": "select", "required": True,
                 "options": ["Athletic shoe", "Running shoe", "Casual sneaker", "Formal shoe",
                            "Boot", "Sandal", "Slipper", "Work boot", "Hiking boot"]}
            ]
        },
        {
            "id": "upper_materials",
            "title": "Upper Materials",
            "repeatable": True,
            "max_items": 5,
            "fields": [
                {"id": "type", "label": "Material Type", "type": "select", "required": True,
                 "options": ["Leather", "Synthetic leather", "Textile - woven", "Textile - knit",
                            "Mesh", "Rubber", "TPU", "Recycled polyester", "Organic cotton"]},
                {"id": "percentage", "label": "Percentage", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True},
                {"id": "origin", "label": "Origin", "type": "select", "required": True,
                 "options": ["Global", "China", "Vietnam", "Indonesia", "India", "Italy", "Brazil", "Europe"]}
            ]
        },
        {
            "id": "sole_materials",
            "title": "Sole Materials",
            "repeatable": True,
            "max_items": 3,
            "fields": [
                {"id": "type", "label": "Material Type", "type": "select", "required": True,
                 "options": ["Rubber - natural", "Rubber - synthetic", "EVA", "TPU", "PU foam",
                            "Cork", "Leather", "Recycled rubber"]},
                {"id": "percentage", "label": "Percentage", "type": "number", "unit": "%", "min": 0, "max": 100, "required": True}
            ]
        },
        {
            "id": "manufacturing",
            "title": "Manufacturing",
            "fields": [
                {"id": "assembly_location", "label": "Assembly Location", "type": "select", "required": True,
                 "options": ["China", "Vietnam", "Indonesia", "India", "Bangladesh", "Italy", "Portugal", "Mexico"]},
                {"id": "cutting_waste", "label": "Cutting Waste", "type": "number", "unit": "%", "required": True},
                {"id": "renewable_energy", "label": "Renewable Energy Use", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "transport",
            "title": "Transportation",
            "fields": [
                {"id": "destination", "label": "Destination Market", "type": "select", "required": True,
                 "options": ["Europe", "North America", "Asia", "Global"]},
                {"id": "primary_mode", "label": "Primary Transport Mode", "type": "select", "required": True,
                 "options": ["Container ship", "Aircraft", "Truck", "Train"]},
                {"id": "distance", "label": "Total Distance", "type": "number", "unit": "km", "required": True}
            ]
        },
        {
            "id": "use_phase",
            "title": "Use Phase",
            "fields": [
                {"id": "include", "label": "Include Use Phase", "type": "boolean", "required": True},
                {"id": "expected_lifetime_years", "label": "Expected Lifetime", "type": "number", "unit": "years", "required": False},
                {"id": "maintenance_frequency", "label": "Maintenance Frequency", "type": "select", "required": False,
                 "options": ["Weekly", "Monthly", "Quarterly", "Rarely"]}
            ]
        },
        {
            "id": "end_of_life",
            "title": "End of Life",
            "fields": [
                {"id": "include", "label": "Include End of Life", "type": "boolean", "required": True},
                {"id": "recycled", "label": "Recycled", "type": "number", "unit": "%", "required": False},
                {"id": "incinerated", "label": "Incinerated", "type": "number", "unit": "%", "required": False},
                {"id": "landfill", "label": "Landfill", "type": "number", "unit": "%", "required": False}
            ]
        }
    ]
}

CONSTRUCTION_SCHEMA = {
    "industry": "construction",
    "name": "Construction Materials LCA Input Schema",
    "description": "Input schema for construction materials LCA",
    "sections": [
        {
            "id": "product",
            "title": "Product Information",
            "fields": [
                {"id": "product_id", "label": "Product ID", "type": "text", "required": True},
                {"id": "description", "label": "Description", "type": "textarea", "required": False},
                {"id": "weight_kg", "label": "Weight", "type": "number", "unit": "kg", "required": True},
                {"id": "product_type", "label": "Product Type", "type": "select", "required": True,
                 "options": ["Concrete", "Steel reinforcement", "Insulation", "Brick", "Glass",
                            "Timber", "Plasterboard", "Roofing material", "Flooring"]}
            ]
        },
        {
            "id": "main_material",
            "title": "Main Material",
            "fields": [
                {"id": "type", "label": "Material Type", "type": "select", "required": True,
                 "options": ["Portland cement", "Recycled aggregate", "Virgin aggregate", "Steel",
                            "Glass wool", "Stone wool", "EPS", "XPS", "PIR", "Wood fiber",
                            "Timber - softwood", "Timber - hardwood", "Clay brick", "Concrete block"]},
                {"id": "recycled_content", "label": "Recycled Content", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "additives",
            "title": "Additives",
            "repeatable": True,
            "max_items": 5,
            "fields": [
                {"id": "type", "label": "Additive Type", "type": "select", "required": True,
                 "options": ["Plasticizer", "Accelerator", "Retarder", "Air entrainer", 
                            "Water reducer", "Pigment", "Fiber reinforcement"]},
                {"id": "percentage", "label": "Percentage", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "manufacturing",
            "title": "Manufacturing",
            "fields": [
                {"id": "production_location", "label": "Production Location", "type": "select", "required": True,
                 "options": ["Local (<50km)", "Regional (50-200km)", "National (200-500km)", "International"]},
                {"id": "energy_source", "label": "Primary Energy Source", "type": "select", "required": True,
                 "options": ["Grid electricity", "Natural gas", "Coal", "Renewable", "Mixed"]},
                {"id": "renewable_share", "label": "Renewable Energy Share", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "transport",
            "title": "Transportation",
            "fields": [
                {"id": "mode", "label": "Transport Mode", "type": "select", "required": True,
                 "options": ["Truck", "Train", "Ship", "Mixed"]},
                {"id": "distance", "label": "Distance to Site", "type": "number", "unit": "km", "required": True}
            ]
        },
        {
            "id": "use_phase",
            "title": "Use Phase",
            "fields": [
                {"id": "include", "label": "Include Use Phase", "type": "boolean", "required": True},
                {"id": "service_life", "label": "Service Life", "type": "number", "unit": "years", "required": False},
                {"id": "maintenance_required", "label": "Maintenance Required", "type": "boolean", "required": False}
            ]
        },
        {
            "id": "end_of_life",
            "title": "End of Life",
            "fields": [
                {"id": "include", "label": "Include End of Life", "type": "boolean", "required": True},
                {"id": "recyclable", "label": "Recyclable", "type": "number", "unit": "%", "required": False},
                {"id": "downcyclable", "label": "Downcyclable", "type": "number", "unit": "%", "required": False},
                {"id": "landfill", "label": "Landfill", "type": "number", "unit": "%", "required": False}
            ]
        }
    ]
}

BATTERY_SCHEMA = {
    "industry": "battery",
    "name": "Battery Systems LCA Input Schema",
    "description": "Input schema for battery systems LCA",
    "sections": [
        {
            "id": "product",
            "title": "Product Information",
            "fields": [
                {"id": "product_id", "label": "Product ID", "type": "text", "required": True},
                {"id": "description", "label": "Description", "type": "textarea", "required": False},
                {"id": "weight_kg", "label": "Weight", "type": "number", "unit": "kg", "required": True},
                {"id": "capacity_kwh", "label": "Capacity", "type": "number", "unit": "kWh", "required": True},
                {"id": "battery_type", "label": "Battery Type", "type": "select", "required": True,
                 "options": ["NMC 111", "NMC 532", "NMC 622", "NMC 811", "LFP", "NCA", "LMO", "Solid State"]}
            ]
        },
        {
            "id": "cathode",
            "title": "Cathode",
            "fields": [
                {"id": "chemistry", "label": "Cathode Chemistry", "type": "select", "required": True,
                 "options": ["NMC (Nickel Manganese Cobalt)", "LFP (Lithium Iron Phosphate)",
                            "NCA (Nickel Cobalt Aluminum)", "LMO (Lithium Manganese Oxide)"]},
                {"id": "percentage", "label": "Mass Percentage", "type": "number", "unit": "%", "required": True},
                {"id": "recycled_content", "label": "Recycled Content", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "anode",
            "title": "Anode",
            "fields": [
                {"id": "material", "label": "Anode Material", "type": "select", "required": True,
                 "options": ["Graphite - natural", "Graphite - synthetic", "Silicon-graphite composite",
                            "Lithium metal", "Lithium titanate"]},
                {"id": "percentage", "label": "Mass Percentage", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "electrolyte",
            "title": "Electrolyte",
            "fields": [
                {"id": "type", "label": "Electrolyte Type", "type": "select", "required": True,
                 "options": ["Liquid - LiPF6", "Solid - polymer", "Solid - ceramic", "Gel"]},
                {"id": "percentage", "label": "Mass Percentage", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "separator",
            "title": "Separator",
            "fields": [
                {"id": "material", "label": "Separator Material", "type": "select", "required": True,
                 "options": ["Polyethylene", "Polypropylene", "Ceramic coated", "Composite"]},
                {"id": "percentage", "label": "Mass Percentage", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "housing",
            "title": "Cell Housing & Pack",
            "fields": [
                {"id": "cell_format", "label": "Cell Format", "type": "select", "required": True,
                 "options": ["Cylindrical", "Prismatic", "Pouch"]},
                {"id": "housing_material", "label": "Housing Material", "type": "select", "required": True,
                 "options": ["Aluminum", "Steel", "Plastic composite"]},
                {"id": "housing_percentage", "label": "Housing Mass Percentage", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "manufacturing",
            "title": "Manufacturing",
            "fields": [
                {"id": "cell_production_location", "label": "Cell Production Location", "type": "select", "required": True,
                 "options": ["China", "South Korea", "Japan", "USA", "Europe", "Global"]},
                {"id": "pack_assembly_location", "label": "Pack Assembly Location", "type": "select", "required": True,
                 "options": ["China", "South Korea", "Japan", "USA", "Europe", "Global"]},
                {"id": "renewable_energy", "label": "Renewable Energy Use", "type": "number", "unit": "%", "required": True}
            ]
        },
        {
            "id": "transport",
            "title": "Transportation",
            "fields": [
                {"id": "destination", "label": "Destination", "type": "select", "required": True,
                 "options": ["Europe", "North America", "Asia", "Global"]},
                {"id": "mode", "label": "Transport Mode", "type": "select", "required": True,
                 "options": ["Container ship", "Truck", "Train", "Aircraft"]},
                {"id": "distance", "label": "Total Distance", "type": "number", "unit": "km", "required": True}
            ]
        },
        {
            "id": "use_phase",
            "title": "Use Phase",
            "fields": [
                {"id": "include", "label": "Include Use Phase", "type": "boolean", "required": True},
                {"id": "application", "label": "Application", "type": "select", "required": False,
                 "options": ["Electric vehicle", "Energy storage", "Consumer electronics", "Industrial"]},
                {"id": "cycle_life", "label": "Expected Cycle Life", "type": "number", "required": False},
                {"id": "efficiency", "label": "Round-trip Efficiency", "type": "number", "unit": "%", "required": False}
            ]
        },
        {
            "id": "end_of_life",
            "title": "End of Life",
            "fields": [
                {"id": "include", "label": "Include End of Life", "type": "boolean", "required": True},
                {"id": "recycling_rate", "label": "Recycling Rate", "type": "number", "unit": "%", "required": False},
                {"id": "second_life", "label": "Second Life Application", "type": "boolean", "required": False},
                {"id": "material_recovery", "label": "Material Recovery Rate", "type": "number", "unit": "%", "required": False}
            ]
        }
    ]
}

INDUSTRY_SCHEMAS = {
    "textile": TEXTILE_SCHEMA,
    "footwear": FOOTWEAR_SCHEMA,
    "construction": CONSTRUCTION_SCHEMA,
    "battery": BATTERY_SCHEMA
}

# ============== API ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "EUFSI LCA Tool API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "initialized"}

# ============== AUTHENTICATION ROUTES ==============

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        company=user_data.company,
        hashed_password=get_password_hash(user_data.password)
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "company": user.company
        }
    }

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login with email and password"""
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "company": user.get("company")
        }
    }

@api_router.get("/auth/me")
async def get_current_user_info(current_user: Dict = Depends(require_auth)):
    """Get current user information"""
    return current_user

# Database info
@api_router.get("/lca/databases")
async def get_databases():
    """Get available LCA databases"""
    return {
        "databases": bw_engine.AVAILABLE_DATABASES,
        "default": "USLCI"
    }

@api_router.get("/lca/methods")
async def get_methods():
    """Get available LCIA methods"""
    return {
        "methods": {
            "ReCiPe": {
                "name": "ReCiPe 2016 Midpoint (H)",
                "categories": list(bw_engine.IMPACT_CATEGORIES["ReCiPe"].keys())
            },
            "EF3.1": {
                "name": "Environmental Footprint 3.1",
                "categories": list(bw_engine.IMPACT_CATEGORIES["EF3.1"].keys())
            }
        },
        "default": "ReCiPe"
    }

@api_router.get("/lca/impact-categories/{method}")
async def get_impact_categories(method: str):
    """Get impact categories for a specific method"""
    if method not in bw_engine.IMPACT_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Method {method} not found")
    
    categories = {}
    for key, info in bw_engine.IMPACT_CATEGORIES[method].items():
        categories[key] = {
            "name": info[1],
            "abbreviation": info[2],
            "unit": info[3]
        }
    return {"method": method, "categories": categories}

# Industry schemas
@api_router.get("/industries")
async def get_industries():
    """Get available industries"""
    return {
        "industries": [
            {"id": "textile", "name": "Textile", "description": "Apparel and textile products"},
            {"id": "footwear", "name": "Footwear", "description": "Shoes and footwear products"},
            {"id": "construction", "name": "Construction", "description": "Construction materials"},
            {"id": "battery", "name": "Battery", "description": "Battery systems and cells"}
        ]
    }

@api_router.get("/industries/{industry}/schema")
async def get_industry_schema(industry: str):
    """Get input schema for an industry"""
    if industry not in INDUSTRY_SCHEMAS:
        raise HTTPException(status_code=404, detail=f"Industry {industry} not found")
    return INDUSTRY_SCHEMAS[industry]

# Projects CRUD
@api_router.post("/projects", response_model=LCAProject)
async def create_project(project: LCAProjectCreate):
    """Create a new LCA project"""
    project_obj = LCAProject(
        name=project.name,
        description=project.description or "",
        industry=project.industry,
        scope=project.scope,
        database=project.database,
        method=project.method,
        product_weight_grams=project.product_weight_grams,
        product_scenario=project.product_scenario
    )
    
    doc = project_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.projects.insert_one(doc)
    return project_obj

@api_router.get("/projects", response_model=List[LCAProject])
async def get_projects():
    """Get all projects"""
    projects = await db.projects.find({}, {"_id": 0}).to_list(1000)
    for p in projects:
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
        if isinstance(p.get('updated_at'), str):
            p['updated_at'] = datetime.fromisoformat(p['updated_at'])
    return projects

@api_router.get("/projects/{project_id}", response_model=LCAProject)
async def get_project(project_id: str):
    """Get a specific project"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if isinstance(project.get('created_at'), str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    if isinstance(project.get('updated_at'), str):
        project['updated_at'] = datetime.fromisoformat(project['updated_at'])
    
    return project

@api_router.put("/projects/{project_id}/input-data")
async def update_project_input_data(project_id: str, input_data: Dict[str, Any]):
    """Update project input data"""
    result = await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "input_data": input_data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Input data updated successfully"}

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    result = await db.projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Also delete associated results
    await db.results.delete_many({"project_id": project_id})
    
    return {"message": "Project deleted successfully"}

# LCA Calculation
@api_router.post("/lca/calculate/{project_id}")
async def calculate_lca(project_id: str, background_tasks: BackgroundTasks):
    """Trigger LCA calculation for a project"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.get('input_data'):
        raise HTTPException(status_code=400, detail="Project has no input data")
    
    # Update status to calculating
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"status": "calculating", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Perform calculation in background
    background_tasks.add_task(perform_lca_calculation, project_id, project)
    
    return {"message": "Calculation started", "status": "calculating"}

async def perform_lca_calculation(project_id: str, project: dict):
    """Perform the actual LCA calculation"""
    try:
        # Convert dict to LCAProject model
        if isinstance(project.get('created_at'), str):
            project['created_at'] = datetime.fromisoformat(project['created_at'])
        if isinstance(project.get('updated_at'), str):
            project['updated_at'] = datetime.fromisoformat(project['updated_at'])
        
        project_obj = LCAProject(**project)
        input_data = project.get('input_data', {})
        
        # Run Brightway2 calculation
        results = bw_engine.calculate_lca(project_obj, input_data)
        
        # Store results
        result_obj = LCAResult(
            project_id=project_id,
            method_name=project_obj.method,
            impact_categories=results['impact_categories'],
            contribution_by_stage=results['contribution_by_stage'],
            total_impact=results['total_impacts'].get('climate_change', 0),
            unit="kg CO2 eq"
        )
        
        result_doc = result_obj.model_dump()
        result_doc['calculated_at'] = result_doc['calculated_at'].isoformat()
        
        await db.results.insert_one(result_doc)
        
        # Update project status
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"status": "completed", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        logger.info(f"LCA calculation completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"LCA calculation failed for project {project_id}: {str(e)}")
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"status": "error", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )

@api_router.get("/lca/results/{project_id}")
async def get_results(project_id: str):
    """Get LCA results for a project"""
    result = await db.results.find_one(
        {"project_id": project_id},
        {"_id": 0},
        sort=[("calculated_at", -1)]
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")
    
    if isinstance(result.get('calculated_at'), str):
        result['calculated_at'] = datetime.fromisoformat(result['calculated_at'])
    
    return result

@api_router.get("/lca/trace/{project_id}")
async def trace_impact_origin(
    project_id: str, 
    impact_category: str = "climate_change", 
    life_cycle_stage: str = "yarn_production"
):
    """
    Trace the origin of an impact result for a specific category and life cycle stage.
    Shows which activities, exchanges, and characterization factors contribute to it.
    
    Example: /api/lca/trace/{project_id}?impact_category=climate_change&life_cycle_stage=yarn_production
    """
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert to project model
    if isinstance(project.get('created_at'), str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    if isinstance(project.get('updated_at'), str):
        project['updated_at'] = datetime.fromisoformat(project['updated_at'])
    
    project_obj = LCAProject(**project)
    input_data = project.get('input_data', {})
    
    # Get the trace
    trace_result = bw_engine.trace_impact_origin(
        project_obj, 
        input_data, 
        impact_category, 
        life_cycle_stage
    )
    
    return trace_result

@api_router.get("/lca/stages/{industry}")
async def get_life_cycle_stages(industry: str):
    """Get available life cycle stages for an industry"""
    stages = {
        'textile': [
            {'id': 'raw_materials', 'name': 'Raw Materials', 'description': 'Fiber production and processing'},
            {'id': 'yarn_production', 'name': 'Yarn Production', 'description': 'Spinning, twisting, winding'},
            {'id': 'fabric_production', 'name': 'Fabric Production', 'description': 'Weaving, knitting, finishing prep'},
            {'id': 'dyeing_finishing', 'name': 'Dyeing & Finishing', 'description': 'Dyeing, printing, finishing'},
            {'id': 'manufacturing', 'name': 'Manufacturing', 'description': 'Cutting, sewing, assembly'},
            {'id': 'transport', 'name': 'Transport', 'description': 'Road, sea, air transport'},
            {'id': 'use_phase', 'name': 'Use Phase', 'description': 'Washing, drying, ironing'},
            {'id': 'end_of_life', 'name': 'End of Life', 'description': 'Recycling, incineration, landfill'},
        ],
        'footwear': [
            {'id': 'raw_materials', 'name': 'Raw Materials', 'description': 'Leather, rubber, textile production'},
            {'id': 'component_production', 'name': 'Component Production', 'description': 'Sole and upper manufacturing'},
            {'id': 'assembly', 'name': 'Assembly', 'description': 'Lasting, cementing, finishing'},
            {'id': 'transport', 'name': 'Transport', 'description': 'Road, sea transport'},
            {'id': 'use_phase', 'name': 'Use Phase', 'description': 'Cleaning, maintenance'},
            {'id': 'end_of_life', 'name': 'End of Life', 'description': 'Recycling, incineration, landfill'},
        ],
        'construction': [
            {'id': 'raw_materials', 'name': 'Raw Materials', 'description': 'Cement, aggregate, steel production'},
            {'id': 'processing', 'name': 'Processing', 'description': 'Mixing, forming, curing'},
            {'id': 'transport', 'name': 'Transport', 'description': 'Road, rail transport'},
            {'id': 'installation', 'name': 'Installation', 'description': 'Site work, installation'},
            {'id': 'use_phase', 'name': 'Use Phase', 'description': 'Maintenance, repair'},
            {'id': 'end_of_life', 'name': 'End of Life', 'description': 'Demolition, recycling, landfill'},
        ],
        'battery': [
            {'id': 'raw_materials', 'name': 'Raw Materials', 'description': 'Lithium, cobalt, nickel extraction'},
            {'id': 'cell_production', 'name': 'Cell Production', 'description': 'Electrode coating, cell assembly'},
            {'id': 'pack_assembly', 'name': 'Pack Assembly', 'description': 'Module assembly, BMS integration'},
            {'id': 'transport', 'name': 'Transport', 'description': 'Road, sea transport'},
            {'id': 'use_phase', 'name': 'Use Phase', 'description': 'Charging losses, thermal management'},
            {'id': 'end_of_life', 'name': 'End of Life', 'description': 'Disassembly, recycling, disposal'},
        ],
    }
    
    if industry not in stages:
        raise HTTPException(status_code=404, detail=f"Industry {industry} not found")
    
    return {'industry': industry, 'stages': stages[industry]}

# PDF Report Generation
@api_router.get("/reports/{project_id}/pdf")
async def generate_pdf_report(project_id: str):
    """Generate PDF report for a project"""
    # Get project and results
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await db.results.find_one(
        {"project_id": project_id},
        {"_id": 0},
        sort=[("calculated_at", -1)]
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#004494'),
        spaceAfter=20
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#004494'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph("EUFSI LCA Report", title_style))
    elements.append(Spacer(1, 20))
    
    # Project Info
    elements.append(Paragraph("Project Information", heading_style))
    project_data = [
        ["Project Name:", project.get('name', 'N/A')],
        ["Industry:", project.get('industry', 'N/A').title()],
        ["Scope:", project.get('scope', 'N/A').replace('-', ' to ').title()],
        ["Database:", project.get('database', 'N/A')],
        ["Method:", project.get('method', 'N/A')],
        ["Product Weight:", f"{project.get('product_weight_grams', 0)} grams"],
    ]
    
    t = Table(project_data, colWidths=[2*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1E293B')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Impact Results
    elements.append(Paragraph("Environmental Impact Results", heading_style))
    
    impact_data = [["Impact Category", "Value", "Unit"]]
    for cat_key, cat_info in result.get('impact_categories', {}).items():
        impact_data.append([
            cat_key.replace('_', ' ').title(),
            f"{cat_info.get('value', 0):.6f}",
            cat_info.get('unit', '')
        ])
    
    t = Table(impact_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004494')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (1, 1), (1, -1), 'Courier'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Contribution Analysis
    elements.append(Paragraph("Contribution by Life Cycle Stage", heading_style))
    
    # Get climate change contributions as example
    climate_contrib = result.get('contribution_by_stage', {}).get('climate_change', {})
    if climate_contrib:
        contrib_data = [["Life Cycle Stage", "Contribution (kg CO2 eq)", "Percentage"]]
        total = sum(climate_contrib.values())
        for stage, value in climate_contrib.items():
            pct = (value / total * 100) if total > 0 else 0
            contrib_data.append([
                stage.replace('_', ' ').title(),
                f"{value:.4f}",
                f"{pct:.1f}%"
            ])
        
        t = Table(contrib_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004494')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (1, 1), (1, -1), 'Courier'),
        ]))
        elements.append(t)
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        f"Generated by EUFSI LCA Tool on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles['Normal']
    ))
    elements.append(Paragraph(
        "Generated by EUFSI LCA Tool",
        styles['Normal']
    ))
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=LCA_Report_{project_id}.pdf"}
    )

# Status endpoint (legacy)
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# Include the router in the main app
app.include_router(api_router)

# Root-level health check for Render deployment
@app.get("/health")
async def root_health_check():
    return {"status": "healthy"}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize Brightway2 on startup"""
    try:
        bw_engine.initialize()
        logger.info("Brightway2 engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Brightway2: {str(e)}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

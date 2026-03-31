DOMAIN_KNOWLEDGE = {
    "Demand Planning": {
        "themes": ["forecast accuracy", "bias", "baseline/statistical forecasting", "collaboration with sales/marketing", "exception handling", "consensus planning"],
        "kpis": ["MAPE", "WAPE", "Forecast Bias", "Forecast Value Added (FVA)"],
        "tools": ["SAP APO", "OMP", "Kinaxis", "O9", "Excel", "Power BI"],
        "language": ["collaborative forecasting", "S&OP input", "historical sales cleaning", "promotional lift", "seasonality"]
    },
    "Supply Planning": {
        "themes": ["capacity", "constraints", "inventory balancing", "service level", "finite planning", "scenario planning"],
        "kpis": ["Order Fulfillment Rate", "Capacity Utilization", "Production Adherence"],
        "tools": ["SAP IBP", "OMP", "Kinaxis", "ERP"],
        "language": ["rough-cut capacity", "production scheduling", "bottleneck management", "material availability", "lead times"]
    },
    "Inventory": {
        "themes": ["safety stock", "reorder logic", "DIO", "stock turns", "service level", "slow/obsolete stock"],
        "kpis": ["Days Inventory Outstanding (DIO)", "Inventory Turns", "Obsolete Stock %", "Service Level / Fill Rate"],
        "tools": ["ERP", "Excel", "Tableau", "Power BI"],
        "language": ["working capital", "ABC/XYZ analysis", "safety stock optimization", "EOQ", "SLOBs"]
    },
    "Logistics": {
        "themes": ["OTIF", "transportation planning", "warehouse coordination", "lead time", "route/service issues"],
        "kpis": ["On-Time In-Full (OTIF)", "Freight Cost per Unit", "Warehouse Utilization", "Transit Time"],
        "tools": ["TMS", "WMS", "SAP TM"],
        "language": ["freight forwarding", "customs clearance", "last-mile delivery", "3PL management", "carrier performance"]
    },
    "Procurement / Buyer": {
        "themes": ["supplier management", "negotiations", "cost savings", "MOQ", "lead times", "supplier risk", "PO management"],
        "kpis": ["Cost Savings (PPV)", "Supplier On-Time Delivery", "Spend Under Management"],
        "tools": ["Ariba", "Coupa", "SAP MM"],
        "language": ["strategic sourcing", "RFx", "vendor scorecards", "contract management", "TCO"]
    },
    "Data Analytics": {
        "themes": ["dashboards", "SQL", "Excel", "Power BI", "Tableau", "root-cause analysis", "KPI storytelling"],
        "kpis": ["Data Accuracy", "Report Adoption Rate", "Time to Insight"],
        "tools": ["SQL", "Power BI", "Tableau", "Python", "Alteryx"],
        "language": ["data pipelines", "data visualization", "predictive analytics", "ETL", "actionable insights"]
    },
    "S&OP / IBP": {
        "themes": ["cross-functional alignment", "executive reporting", "scenario planning", "balancing supply and demand"],
        "kpis": ["EBITDA impact", "Consensus Forecast Accuracy", "Working Capital"],
        "tools": ["SAP IBP", "O9", "Kinaxis", "Power BI"],
        "language": ["demand review", "supply review", "executive S&OP", "gap closing", "financial integration"]
    },
    "ERP / Planning Systems": {
        "themes": ["business requirement gathering", "testing/UAT", "change management", "training", "cutover", "master data", "process mapping"],
        "kpis": ["System Adoption", "Data Defect Rate", "Project Go-Live Status"],
        "tools": ["SAP", "OMP", "Kinaxis RapidResponse", "O9"],
        "language": ["fit-gap analysis", "functional specs", "super user", "hypercare", "system landscape"]
    },
    "Master Data": {
        "themes": ["data governance", "data accuracy", "ERP master data", "process discipline", "cross-functional coordination"],
        "kpis": ["Master Data Accuracy", "Data Creation Lead Time", "Duplicate Records %"],
        "tools": ["SAP MDG", "Informatica", "Excel"],
        "language": ["material master", "BOM", "routings", "data stewardship", "data taxonomy"]
    }
}

def detect_role_family(text: str) -> str:
    """Heuristically determines the closest role family from a text (JD or Job Title)."""
    text = text.lower()

    # Direct matches
    if "demand plan" in text or "forecast" in text: return "Demand Planning"
    if "supply plan" in text or "capacity" in text: return "Supply Planning"
    if "inventory" in text or "stock" in text: return "Inventory"
    if "logistic" in text or "transport" in text or "warehouse" in text or "distribution" in text: return "Logistics"
    if "procure" in text or "buyer" in text or "purchas" in text or "sourcing" in text: return "Procurement / Buyer"
    if "analy" in text or "data" in text or "power bi" in text or "tableau" in text: return "Data Analytics"
    if "s&op" in text or "ibp" in text or "sales and operations" in text: return "S&OP / IBP"
    if "erp" in text or "implement" in text or "project" in text or "transformation" in text: return "ERP / Planning Systems"
    if "master data" in text or "governance" in text: return "Master Data"

    # Fallback to a general role if not explicitly detected
    return "Supply Chain Generalist"

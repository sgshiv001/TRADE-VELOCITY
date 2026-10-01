"""A small, curated NSE company universe; no generated financial fundamentals."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Company:
    symbol: str
    name: str
    sector: str
    description: str
    website: str
    color: str

    @property
    def ticker(self) -> str:
        return f"{self.symbol}.NS"

    @property
    def quote_url(self) -> str:
        return f"https://finance.yahoo.com/quote/{self.ticker}/"


COMPANIES = {
    company.symbol: company for company in (
        Company("RELIANCE", "Reliance Industries", "Diversified", "An Indian group spanning energy, petrochemicals, retail, and digital services.", "https://www.ril.com/about", "#60a5fa"),
        Company("TCS", "Tata Consultancy Services", "Technology", "IT services, consulting, and business solutions for organizations worldwide.", "https://www.tcs.com/who-we-are", "#a78bfa"),
        Company("INFY", "Infosys", "Technology", "Digital services and consulting, including software development and enterprise transformation.", "https://www.infosys.com/about.html", "#38bdf8"),
        Company("HDFCBANK", "HDFC Bank", "Banking", "An Indian bank serving retail customers and businesses with banking and financial services.", "https://www.hdfc.bank.in/about-us", "#fb7185"),
        Company("ICICIBANK", "ICICI Bank", "Banking", "Banking and financial services for individuals, businesses, and corporations.", "https://www.icici.bank.in/about-us", "#fb923c"),
        Company("BHARTIARTL", "Bharti Airtel", "Telecommunications", "Telecommunications services, including mobile connectivity, broadband, and enterprise networks.", "https://www.airtel.in/", "#f472b6"),
        Company("LT", "Larsen & Toubro", "Industrials", "Engineering, construction, manufacturing, and technology businesses.", "https://www.larsentoubro.com/corporate/about-lt-group", "#fbbf24"),
        Company("ITC", "ITC", "Consumer goods", "An Indian group with FMCG, paperboards and packaging, agriculture, and IT businesses.", "https://itcportal.com/about-itc/our-profile.html", "#34d399"),
    )
}

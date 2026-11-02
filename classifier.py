"""
CiviNexa AI - Intelligent Civic Issue Classification Engine
Module: classifier.py

This module analyzes civic complaints (title and description) using natural
language processing and weighted semantic keyword matching to accurately
predict the civic issue category and recommend the responsible municipal department.
Designed to be modular and easily extensible to machine learning or LLM APIs.
"""

import re
from typing import Dict, List, Any


class CivicIssueClassifier:
    """
    AI-powered civic issue classifier that parses complaint text, computes category
    relevance scores, detects urgency signals, and maps to the appropriate civic authority.
    """

    CATEGORIES_CONFIG = {
        "Road Maintenance": {
            "department": "Department of Roads & Infrastructure / Public Works (PWD)",
            "icon": "bi-cone-striped",
            "base_priority": "Medium",
            "keywords": {
                "pothole": 4, "potholes": 4, "crater": 4, "craters": 4, "road": 3, "roads": 3,
                "street": 2, "asphalt": 3, "tar": 2, "concrete": 2, "pavement": 3, "footpath": 3,
                "crack": 3, "cracks": 3, "caved": 4, "cave-in": 5, "sinkhole": 5,
                "speed breaker": 4, "bump": 3, "bumps": 3, "uneven": 3, "damaged road": 4,
                "broken road": 4, "divider": 2, "traffic divider": 3, "gravel": 3, "resurfacing": 3,
                "highway": 3, "lane": 2, "sidewalk": 3, "culvert": 3, "bridge": 3, "kerb": 2
            },
            "urgent_indicators": ["sinkhole", "huge crater", "cave-in", "fatal", "accident zone", "collapsed road"]
        },
        "Waste Management": {
            "department": "Municipal Solid Waste Management & Sanitation Dept.",
            "icon": "bi-trash3",
            "base_priority": "Medium",
            "keywords": {
                "garbage": 5, "trash": 5, "waste": 4, "dump": 4, "dumped": 4, "dumping": 4,
                "dumpyard": 4, "debris": 3, "litter": 4, "dustbin": 4, "dustbins": 4, "bin": 3, "bins": 3,
                "overflowing bin": 5, "rotten": 3, "smell": 3, "stench": 4, "stink": 4,
                "foul odor": 4, "plastic": 3, "solid waste": 5, "sanitation": 4,
                "cleaning": 3, "sweeping": 3, "uncollected": 4, "rubbish": 4, "refuse": 2,
                "bio waste": 4, "carcass": 5, "dead animal": 5, "scrap": 3, "filth": 4, "swill": 3
            },
            "urgent_indicators": ["carcass", "dead animal", "hospital waste", "biohazard", "toxic dump"]
        },
        "Drainage & Sewage": {
            "department": "Sewage, Stormwater & Drainage Board",
            "icon": "bi-water",
            "base_priority": "High",
            "keywords": {
                "drain": 5, "drainage": 5, "drains": 4, "sewer": 5, "sewage": 5, "sewers": 5,
                "gutter": 4, "gutters": 4, "manhole": 4, "manholes": 4, "open manhole": 6,
                "clogged": 4, "clog": 4, "choked": 4, "blocked drain": 5, "overflow": 4, "overflowing": 5,
                "waterlogging": 5, "waterlogged": 5, "stagnant": 4, "black water": 4, "cesspool": 4,
                "septic": 4, "sludge": 3, "drain choke": 5, "culvert choked": 4, "stormwater": 4
            },
            "urgent_indicators": ["open manhole", "flooding houses", "sewage backflow into homes", "overflowing hospital"]
        },
        "Electricity & Lighting": {
            "department": "City Electricity Board & Public Lighting Authority",
            "icon": "bi-lightbulb",
            "base_priority": "Medium",
            "keywords": {
                "streetlight": 5, "streetlights": 5, "street light": 5, "street lights": 5,
                "lamp": 4, "lamppost": 4, "light": 2, "lighting": 3, "dark": 3, "darkness": 4,
                "flickering": 4, "not working": 2, "unlit": 4,
                "electricity": 4, "electric": 4, "loose wire": 5, "hanging wire": 5,
                "sparking": 6, "sparks": 5, "transformer": 5, "power outage": 4, "blackout": 4,
                "short circuit": 6, "live wire": 6, "cable": 3, "cables": 3, "pole": 3, "electric pole": 5,
                "electric shock": 6, "meter box": 3
            },
            "urgent_indicators": ["live wire", "hanging wire", "sparking", "electric shock", "short circuit"]
        },
        "Water Supply": {
            "department": "Public Water Supply & Sewerage Board (Jal Board)",
            "icon": "bi-droplet-half",
            "base_priority": "High",
            "keywords": {
                "water": 3, "drinking water": 5, "water supply": 5, "pipe": 4, "pipes": 4,
                "pipeline": 5, "pipe burst": 6, "burst pipe": 6, "leak": 4, "leakage": 5,
                "leaking": 5, "leaks": 4, "burst": 4, "tap": 4, "public tap": 5, "faucet": 3,
                "pressure": 3, "low pressure": 4, "no water": 5, "water cut": 4,
                "contaminated water": 5, "dirty water": 4, "muddy water": 4, "chlorine": 3,
                "tanker": 3, "water tanker": 4, "valve": 3, "hydrant": 4, "water shortage": 5
            },
            "urgent_indicators": ["pipe burst", "contaminated water", "massive leakage", "drinking water poison", "zero water"]
        },
        "Public Infrastructure": {
            "department": "Urban Development & Civic Infrastructure Directorate",
            "icon": "bi-building-gear",
            "base_priority": "Low",
            "keywords": {
                "bench": 4, "benches": 4, "park": 3, "parks": 3, "garden": 3, "playground": 4,
                "swings": 4, "slide": 3, "bus stop": 5, "bus shelter": 5, "shelter": 3,
                "railing": 4, "railings": 4, "fence": 3, "fencing": 3, "footbridge": 5,
                "overbridge": 4, "public toilet": 5, "urinal": 4, "toilets": 4,
                "signboard": 4, "road sign": 4, "traffic signal": 5, "signal broken": 5,
                "zebra crossing": 4, "community hall": 3, "boundary wall": 3, "vandalism": 4,
                "infrastructure": 4, "public property": 4
            },
            "urgent_indicators": ["footbridge collapse", "broken railing on bridge", "traffic signal broken"]
        }
    }

    CONFIDENCE_THRESHOLD = 3.0  # Minimum aggregated score required to assign category

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Sanitizes and normalizes text for analysis."""
        if not text:
            return ""
        text = text.lower()
        # Replace multiple whitespace and non-alphanumeric except hyphen and space
        text = re.sub(r'[^a-z0-9\s\-]', ' ', text)
        return " " + re.sub(r'\s+', ' ', text).strip() + " "

    @classmethod
    def classify(cls, description: str, title: str = "") -> Dict[str, Any]:
        """
        Classifies the complaint based on its title and description.
        Returns a dict with category, department, confidence, matched keywords, priority, and icon.
        """
        combined_text = f"{title} {description}"
        norm_text = cls.clean_text(combined_text)

        if not norm_text.strip():
            return {
                "category": "Needs Manual Review",
                "department": "General Grievance Redressal & Triage Cell",
                "confidence": 0.0,
                "confidence_percent": 0,
                "matched_keywords": [],
                "priority": "Medium",
                "icon": "bi-question-circle",
                "explanation": "No sufficient text was provided to classify the issue."
            }

        scores: Dict[str, float] = {}
        matched_dict: Dict[str, List[str]] = {}
        urgent_matches: List[str] = []

        for category, config in cls.CATEGORIES_CONFIG.items():
            cat_score = 0.0
            cat_matched = []

            # Check keyword matches
            for kw, weight in config["keywords"].items():
                pattern = r'(?:\b|[\s\-])' + re.escape(kw) + r'(?:\b|[\s\-])'
                matches = len(re.findall(pattern, norm_text))
                if matches > 0:
                    cat_score += weight * matches
                    cat_matched.append(kw)

            # Check urgent indicator phrases
            for urgent_kw in config["urgent_indicators"]:
                if urgent_kw in norm_text:
                    urgent_matches.append(urgent_kw)
                    cat_score += 3.0

            scores[category] = cat_score
            matched_dict[category] = cat_matched

        # Find best category
        sorted_categories = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        best_category, highest_score = sorted_categories[0]

        # Calculate normalized confidence (0 to 100%)
        # Scale: score 3 is ~50%, score 10+ is ~95%
        confidence_percent = min(round((highest_score / (highest_score + 3.0)) * 100), 98) if highest_score > 0 else 0

        if highest_score < cls.CONFIDENCE_THRESHOLD:
            return {
                "category": "Needs Manual Review",
                "department": "General Grievance Redressal & Triage Cell",
                "confidence": round(highest_score, 2),
                "confidence_percent": confidence_percent,
                "matched_keywords": matched_dict.get(best_category, []),
                "priority": "Medium",
                "icon": "bi-question-circle",
                "explanation": "The issue description is unclear or does not match predefined civic categories. Flagged for human review."
            }

        config = cls.CATEGORIES_CONFIG[best_category]
        priority = config["base_priority"]

        # Elevate priority if urgency triggers detected
        if urgent_matches:
            priority = "Urgent"
        elif highest_score >= 10 and priority == "Medium":
            priority = "High"

        explanation = (
            f"Classified as '{best_category}' based on matched keywords: "
            f"{', '.join(matched_dict[best_category][:4])}. "
            f"Assigned to {config['department']} with {priority} priority."
        )

        return {
            "category": best_category,
            "department": config["department"],
            "confidence": round(highest_score, 2),
            "confidence_percent": confidence_percent,
            "matched_keywords": matched_dict[best_category],
            "priority": priority,
            "icon": config["icon"],
            "explanation": explanation
        }


# Convenience function
def classify_issue(description: str, title: str = "") -> Dict[str, Any]:
    return CivicIssueClassifier.classify(description=description, title=title)


if __name__ == "__main__":
    # Test suite for quick CLI verification
    test_cases = [
        "There is a big pothole on the road near the junction causing traffic issues",
        "Garbage is collected near the park and smelling terrible, overflowing bin",
        "Drain water is overflowing from the manhole and flooding the street",
        "Streetlight is not working and the whole street is completely dark",
        "Water is leaking from a public pipe on 5th avenue",
        "Broken bench in municipal park and damaged swings",
        "Hello I need some general help with my tax"
    ]

    print("=== Testing CivicIssueClassifier ===")
    for test in test_cases:
        res = classify_issue(test)
        print(f"\nText: {test}")
        print(f" -> Category: {res['category']}")
        print(f" -> Dept: {res['department']}")
        print(f" -> Confidence: {res['confidence_percent']}% | Priority: {res['priority']}")

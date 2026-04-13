import re

class PredictionService:
    STOP_WORDS = {
        "a", "about", "above", "across", "after", "afterwards", "again", "against", "all", "almost", "alone",
        "along", "already", "also", "although", "always", "am", "among", "amongst", "amoungst", "amount", "an",
        "and", "another", "any", "anyhow", "anyone", "anything", "anyway", "anywhere", "are", "around", "as",
        "at", "back", "be", "became", "because", "become", "becomes", "becoming", "been", "before", "beforehand",
        "behind", "being", "below", "beside", "besides", "between", "beyond", "bill", "both", "bottom", "but",
        "by", "call", "can", "cannot", "cant", "co", "con", "could", "couldnt", "cry", "de", "describe", "detail",
        "do", "done", "down", "due", "during", "each", "eg", "eight", "either", "eleven", "else", "elsewhere",
        "empty", "enough", "etc", "even", "ever", "every", "everyone", "everything", "everywhere", "except", "few",
        "fifteen", "fify", "fill", "find", "fire", "first", "five", "for", "former", "formerly", "forty", "found",
        "four", "from", "front", "full", "further", "get", "give", "go", "had", "has", "hasnt", "have", "he",
        "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", "hers", "herself", "him", "himself",
        "his", "how", "however", "hundred", "ie", "if", "in", "inc", "indeed", "interest", "into", "is", "it",
        "its", "itself", "keep", "last", "latter", "latterly", "least", "less", "ltd", "made", "many", "may", "me",
        "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly", "move", "much", "must", "my",
        "myself", "name", "namely", "neither", "never", "nevertheless", "next", "nine", "no", "nobody", "none",
        "noone", "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on", "once", "one", "only",
        "onto", "or", "other", "others", "otherwise", "our", "ours", "ourselves", "out", "over", "own", "part",
        "per", "perhaps", "please", "put", "rather", "re", "same", "see", "seem", "seemed", "seeming", "seems",
        "serious", "several", "she", "should", "show", "side", "since", "sincere", "six", "sixty", "so", "some",
        "somehow", "someone", "something", "sometime", "sometimes", "somewhere", "still", "such", "system", "take",
        "ten", "than", "that", "the", "their", "them", "themselves", "then", "thence", "there", "thereafter",
        "thereby", "therefore", "therein", "thereupon", "these", "they", "thickv", "thin", "third", "this", "those",
        "though", "three", "through", "throughout", "thru", "thus", "to", "together", "too", "top", "toward",
        "towards", "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us", "very", "via", "was",
        "we", "well", "were", "what", "whatever", "when", "whence", "whenever", "where", "whereafter", "whereas",
        "whereby", "wherein", "whereupon", "wherever", "whether", "which", "while", "whither", "who", "whoever",
        "whole", "whom", "whose", "why", "will", "with", "within", "without", "would", "yet", "you", "your",
        "yours", "yourself", "yourselves", "the"
    }

    SYMPTOMS = {
        "frothy-salivation", "reduced-appetite", "resistance-oralExamination", "mouth-ulcer", "vesicles",
        "gas-bloat", "ptyyalism", "nasal-discharge", "asphyxia", "bruxism", "bloat", "increased-salivation",
        "difficulty-swallowing", "shallow-breathing", "coughing", "anorexia", "recurrent-bloat", "decreased-milk",
        "weight-loss", "diarrhea", "Increased-heart-rate", "Increased-breathing", "decreased-rumen-motility", "fever",
        "poorly-digested", "pain", "dysentery", "abdominal-pain", "mucosal-damage", "mucosal-petechiation",
        "GI-hemorrhage", "sunken-eyes", "twisting-stomach", "rectal-pain", "bleeding", "discharge", "sever-anemia",
        "diarrhoea", "Anemia", "colic-diarrhoea", "respiratory-noise", "dysphagia", "Increased-respiratory-rate",
        "dyspnea", "constipation", "grey/white-skin", "ash-skin", "red-patches", "red-patch", "papules", "nodules",
        "hair-loss", "thickened-skin", "lesions", "itching", "skin-thicken", "folds", "Pruritus", "alopatia",
        "vulvar-swelling", "labia-swelling", "vulvar-discharge", "vaginal-mucosa", "straining-urination",
        "grayish-discharge", "pale-yellow-discharge", "weakness", "fowl-smell", "arch-back", "deacreased-urination",
        "uterus-pus", "discharge-vulva", "swelling-abdomen", "enlarged-uterus", "red-brown-fluid", "uterine-discharge",
        "foetid-odour", "laminitis", "infection-uterus", "focal-hemorrhages", "subcutaneous-tissues", "bleeding-spots",
        "blood-from-skin", "tearing", "spasms-lids", "squinting", "spilling-tears", "epiphora", "avoidance-sunlight",
        "photophobia", "redness", "discharge-eye", "corneal-ulcers", "weeping", "closure-pain", "cornea-cloudy",
        "cornea-white", "eye-pain", "bleeding-nostril", "bleeding-eyeball", "bloody", "ulcerated", "friable",
        "foul-smelling", "mass-eye", "snoring", "febrile", "ear-pain", "head-shaking", "facial-nerve-paralysis",
        "red-gum", "salivation", "difficult-open-mouth", "staggering", "trembling", "convulsions", "swollen-thigh",
        "sound-thigh", "swelling-throat", "drooling", "slobbering", "smacking-lips", "shivering", "sore-feet",
        "blisters", "swollen-udder", "flabes", "blood-millshardness", "reddening", "abortion", "high-fever",
        "ocular-discharge", "eye-discharge", "seizures", "coffee-colour-urine", "jaundice", "brown-urine", "aggression",
        "rapid-pulse", "tachypnoea", "anaemia", "hypoglucemia", "seizure", "impaired-coordination", "lameness",
        "hyper-salivation", "choking", "aggressive-behavior", "attacking-animals"
    }

    def tokenize(self, input_str: str) -> set[str]:
        cleaned = re.sub(r'[,\?:\(\)\.]', ' ', input_str)
        parts = cleaned.split()
        tokens = set()
        for p in parts:
            p_lower = p.lower()
            if p_lower not in self.STOP_WORDS:
                tokens.add(p_lower)
        return tokens

    def predict_disease(self, input_str: str) -> str:
        if not input_str or not input_str.strip():
            return "Invalid Data"

        tokens = self.tokenize(input_str)

        def contains(*words):
            return any(w.lower() in tokens for w in words)

        if contains("frothy-salivation", "reduced-appetite", "resistance-oralExamination", "mouth-ulcer", "vesicles"): return "stomatitis"
        if contains("gas-bloat", "ptyyalism", "nasal-discharge", "asphyxia", "bruxism"): return "esophagitis"
        if contains("bloat", "increased-salivation", "difficulty-swallowing", "shallow-breathing", "coughing"): return "choke"
        if contains("anorexia", "recurrent-bloat", "decreased-milk", "weight-loss"): return "ruminal impaction"
        if contains("reduced-appetite", "diarrhea", "Increased-heart-rate", "Increased-breathing"): return "ruminal acidosis"
        if contains("decreased-rumen-motility", "fever", "poorly-digested", "pain"): return "traumatic reticulopericarditis"
        if contains("diarrhea", "dysentery", "abdominal-pain", "mucosal-damage", "mucosal-petechiation", "GI-hemorrhage"): return "enteritis"
        if contains("anorexia", "decreased-milk", "sunken-eyes", "twisting-stomach"): return "volvulus"
        if contains("rectal-pain", "diarrhea", "bleeding", "discharge"): return "proctitis"
        if contains("sever-anemia", "diarrhoea", "reduced-appetite"): return "tape worm infection"
        if contains("Anemia", "colic-diarrhoea"): return "round worm infection"
        if contains("respiratory-noise", "nasal-discharge", "coughing", "dysphagia"): return "pharyngitis"
        if contains("reduced-appetite", "Increased-respiratory-rate", "cough", "nasal-discharge"): return "pneumonia"
        if contains("cough", "dyspnea", "anorexia", "constipation"): return "bronchitis"
        if contains("grey/white-skin", "ash-skin", "red-patches", "red-patch"): return "ringworm"
        if contains("papules", "nodules", "hair-loss", "thickened-skin", "itching"): return "demodicosis"
        if contains("skin-thicken", "folds", "Pruritus"): return "scabies"
        if contains("vulvar-swelling", "labia-swelling", "vulvar-discharge", "vaginal-mucosa"): return "vaginitis"
        if contains("grayish-discharge", "pale-yellow-discharge", "weakness"): return "cervicitis"
        if contains("fowl-smell", "arch-back", "deacreased-urination"): return "pyometra"
        if contains("uterus-pus", "discharge-vulva", "swelling-abdomen"): return "endometritis"
        if contains("enlarged-uterus", "red-brown-fluid", "uterine-discharge", "foetid-odour"): return "metritis"
        if contains("laminitis", "constipation", "infection-uterus"): return "septic-metritis"
        if contains("focal-hemorrhages", "subcutaneous-tissues", "bleeding-spots", "blood-from-skin"): return "filariasis"
        if contains("tearing", "spasms-lids", "squinting", "spilling-tears", "epiphora", "avoidance-sunlight", "photophobia"): return "corneal-opacity"
        if contains("weeping", "closure-pain", "cornea-cloudy", "cornea-white"): return "conjunctivitis"
        if contains("bleeding-nostril", "bleeding-eyeball"): return "frontal-epithelium"
        if contains("bloody", "ulcerated", "friable", "foul-smelling"): return "squamous-cell-carcinoma"
        if contains("dyspnoea", "snoring", "nodules"): return "nasal-granuloma"
        if contains("febrile", "anorectic", "ear-pain", "facial-nerve-paralysis"): return "otitis"
        if contains("red-gum", "salivation", "difficult-open-mouth"): return "gingivitis"
        if contains("staggering", "trembling", "breathing-difficulty", "convulsions"): return "anthrax"
        if contains("swollen-thigh", "sound-thigh"): return "black-quarter"
        if contains("salivation", "nasal-discharge", "swelling-throat", "drooling"): return "hemorrhagic-septicemia"
        if contains("slobbering", "smacking-lips", "shivering", "sore-feet"): return "foot-mouth-disease"
        if contains("swollen-udder", "flabes", "blood-millshardness", "reddening"): return "mastitis"
        if contains("abortion", "fowl-smell"): return "brucellosis"
        if contains("high-fever", "diarrhea", "ocular-discharge", "eye-discharge"): return "bovine-malignant-catarrhal-fever"
        if contains("coffee-colour-urine", "anorexia", "diarrhea"): return "babesiosis"
        if contains("jaundice", "anorexia", "brown-urine", "aggression"): return "anaplasmosis"
        if contains("tachypnoea", "anaemia"): return "theileriosis"
        if contains("hypoglucemia", "seizure", "anemia"): return "trypanosomiasis"
        if contains("anorexia", "itching", "impaired-coordination", "lameness"): return "rabies"

        return "Invalid Data"

    def get_treatment(self, disease: str) -> str:
        treatments = {
            "stomatitis": "oxytetracycline/Melonex/Boroglycerine",
            "esophagitis": "streptopenicillin/Melonex",
            "choke": "streptopenicillin/Melonex/CPM",
            "ruminal impaction": "Bovilax/Ecotas-bolus/Ketonex-bolus/MgSO4",
            "ruminal acidosis": "sodium-bicarbonate/Bufzone-powder/Ecotas-bolus/Ketonex-bolus",
            "traumatic reticulopericarditis": "Better-Surgery/streptopenicillin/melonex",
            "enteritis": "Intamox/Enrofloxacin/RL-fluids/DNS-fluids",
            "volvulus": "surgery/Enrofloxacin/Melonex/CPM",
            "proctitis": "Enrofloxacin/Melonex/DNS/5%Dextrose",
            "tape worm infection": "Praziquantel/Albendazole/Fenbendazole",
            "round worm infection": "Ivermectin/Doramectin/Levamisole",
            "pharyngitis": "Antibiotics/NSAIDs/Warm-compress",
            "pneumonia": "Tilmicosin/Florfenicol/Enrofloxacin/Flunixin",
            "bronchitis": "Broad-spectrum antibiotics/Bronchodilators/Corticosteroids",
            "ringworm": "Topical antifungals (Miconazole)/Iodine/Griseofulvin",
            "demodicosis": "Amitraz dips/Ivermectin injection",
            "scabies": "Ivermectin/Doramectin/Moxidectin pours",
            "vaginitis": "Mild antiseptic douches/Systemic antibiotics if severe",
            "cervicitis": "Intrauterine antibiotics/Lytalyse (Prostaglandin)",
            "pyometra": "PGF2 alpha (Prostaglandin)/Systemic antibiotics/Fluid therapy",
            "endometritis": "Intrauterine infusions (Cephapirin)/Systemic penicillin",
            "metritis": "Ceftiofur/Penicillin/Oxytetracycline/Supportive care",
            "septic-metritis": "Aggressive IV fluids/Broad-spectrum IV antibiotics/NSAIDs",
            "filariasis": "Diethylcarbamazine/Ivermectin",
            "corneal-opacity": "Topical antibiotics/Subconjunctival penicillin/Vitamin A",
            "conjunctivitis": "Topical oxytetracycline eye ointment/Fly control",
            "frontal-epithelium": "Surgical debridement/Topical antibiotics",
            "squamous-cell-carcinoma": "Surgical excision/Cryotherapy/Radiation",
            "nasal-granuloma": "Sodium iodide IV/Surgical removal/Antihistamines",
            "otitis": "Ear cleaning/Topical antibiotic-steroid/Systemic antibiotics",
            "gingivitis": "Oral hygiene/Soft diet/Broad-spectrum antibiotics",
            "anthrax": "High-dose Penicillin G/Oxytetracycline (Notify Authorities!)",
            "black-quarter": "Penicillin G/Aggressive surgical debridement/Vaccination",
            "hemorrhagic-septicemia": "Sulphadimidine/Oxytetracycline/Enrofloxacin",
            "foot-mouth-disease": "Symptomatic care/Mild mouth wash/Antipyretics (Quarantine)",
            "mastitis": "Intramammary antibiotics (Amoxicillin/Cloxacillin)/Systemic NSAIDs",
            "brucellosis": "No effective treatment; Test and cull (Zoonotic Warning)",
            "bovine-malignant-catarrhal-fever": "Supportive fluid therapy/NSAIDs (Often fatal)",
            "babesiosis": "Diminazene aceturate/Imidocarb dipropionate/Blood transfusion",
            "anaplasmosis": "Oxytetracycline (LA)/Blood transfusion/Iron supplements",
            "theileriosis": "Buparvaquone/Oxytetracycline/Tick control",
            "trypanosomiasis": "Diminazene aceturate/Isometamidium chloride/Suramin",
            "rabies": "No treatment; Fatal. Prevent via vaccination. (Zoonotic Warning, Isolate)"
        }
        return treatments.get(disease, "Consult a Veterinary Doctor for an updated treatment plan.")

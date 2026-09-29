"""
Multilingual Medical Terminology Dictionary for RetinaGuard AI.
Supported Languages: English (en), Tamil (ta), Hindi (hi).
Provides precise medical translations for DR Severity Classes, Lesion Types, and Referral Actions.
"""

TRANSLATIONS = {
    "en": {
        "app_title": "RetinaGuard AI - DR Severity & Lesion Decision Support",
        "disclaimer_banner": "AI-Assisted Preliminary Screening Tool. Does NOT replace an ophthalmologist or provide a definitive medical diagnosis.",
        "nav_dashboard": "Dashboard",
        "nav_new_screening": "New Screening",
        "nav_history": "Screening History",
        "quality_pass": "Image Quality: Acceptable for Analysis",
        "quality_fail": "Image Quality: Insufficient for Reliable Analysis",
        "recapture_title": "Recapture Guidance",
        "icdr_0": "No Apparent DR (Grade 0)",
        "icdr_1": "Mild NPDR (Grade 1)",
        "icdr_2": "Moderate NPDR (Grade 2)",
        "icdr_3": "Severe NPDR (Grade 3)",
        "icdr_4": "Proliferative DR - PDR (Grade 4)",
        "action_0": "No DR detected by AI model. Continue routine annual screening per clinical guidelines.",
        "action_1": "Mild diabetic retinal changes detected. Professional follow-up in 6 to 12 months.",
        "action_2": "Moderate non-proliferative changes detected. Professional eye evaluation recommended in 3 to 6 months.",
        "action_3": "Severe non-proliferative changes detected. Prompt ophthalmic evaluation recommended in 1 to 4 weeks.",
        "action_4": "Findings concerning for proliferative DR detected. Urgent retina specialist evaluation recommended in 1 to 2 weeks.",
        "lesion_exudates": "Hard Exudates (Lipid Deposits)",
        "lesion_hemorrhages": "Retinal Hemorrhages",
        "lesion_microaneurysms": "Microaneurysms",
        "lesion_cws": "Cotton-Wool Spots (Soft Exudates)",
        "view_original": "Original Fundus Photograph",
        "view_annotated": "Lesion Bounding Box Annotations",
        "view_heatmap": "Grad-CAM Saliency Heatmap",
        "view_combined": "Combined Layered Inspection",
        "safety_disclaimer": (
            "IMPORTANT NOTICE: RetinaGuard AI is an AI-assisted screening decision-support software. "
            "This result is not a definitive diagnosis and should be interpreted by a qualified eye-care professional."
        )
    },
    "ta": {
        "app_title": "ரெட்டினாகார்டு AI - விழித்திரை பாதிப்பு நிலை மற்றும் தழும்புகள் பரிசோதனை",
        "disclaimer_banner": "AI-உதவி முதற்கட்ட பரிசோதனை கருவி. இது கண் மருத்துவருக்கு மாற்றாகாது அல்லது இறுதியான மருத்துவக் கண்டறிதல் அல்ல.",
        "nav_dashboard": "முகப்பு பலகை",
        "nav_new_screening": "புதிய பரிசோதனை",
        "nav_history": "பரிசோதனை வரலாறு",
        "quality_pass": "படத்தின் தரம்: பரிசோதனைக்கு ஏற்றது",
        "quality_fail": "படத்தின் தரம்: நம்பிக்கையான ஆய்விற்கு போதுமானதாக இல்லை",
        "recapture_title": "மீண்டும் படம் எடுப்பதற்கான வழிகாட்டுதல்",
        "icdr_0": "நீரிழிவு விழித்திரை பாதிப்பு இல்லை (No Apparent DR - Grade 0)",
        "icdr_1": "மிதமான ஆரம்பக்கட்ட NPDR (Mild NPDR - Grade 1)",
        "icdr_2": "நடுத்தர NPDR (Moderate NPDR - Grade 2)",
        "icdr_3": "கடுமையான Non-Proliferative Diabetic Retinopathy (Severe NPDR - Grade 3)",
        "icdr_4": "அதிதீவிர Proliferative Diabetic Retinopathy (PDR - Grade 4)",
        "action_0": "AI மாதிரியால் பாதிப்பு எதுவும் கண்டறியப்படவில்லை. வருடாந்திர வழக்கமான பரிசோதனையைத் தொடரவும்.",
        "action_1": "ஆரம்பக்கட்ட விழித்திரை மாற்றங்கள் கண்டறியப்பட்டுள்ளன. 6 முதல் 12 மாதங்களுக்குள் மருத்துவப் பரிசோதனை செய்யவும்.",
        "action_2": "நடுத்தர விழித்திரை மாற்றங்கள் கண்டறியப்பட்டுள்ளன. 3 முதல் 6 மாதங்களுக்குள் கண் மருத்துவ ஆலோசன பெறவும்.",
        "action_3": "கடுமையான விழித்திரை மாற்றங்கள் கண்டறியப்பட்டுள்ளன. 1 முதல் 4 வாரங்களுக்குள் அவசர கண் மருத்துவரைப் பார்க்கவும்.",
        "action_4": "அதிதீவிர விழித்திரை பாதிப்பு அறிகுறிகள் கண்டறியப்பட்டுள்ளன. 1 முதல் 2 வாரங்களுக்குள் உடனடியாக கண் சிறப்பு மருத்துவரைப் பார்க்கவும்.",
        "lesion_exudates": "கடினமான கொழுப்புப் படிவுகள் (Hard Exudates)",
        "lesion_hemorrhages": "விழித்திரைக் ரத்தக் கசிவு (Retinal Hemorrhages)",
        "lesion_microaneurysms": "நுண் ரத்தக் குழாய் வீக்கம் (Microaneurysms)",
        "lesion_cws": "பஞ்சு போன்ற வெள்ளை தழும்புகள் (Cotton-Wool Spots)",
        "view_original": "அசல் விழித்திரைப் படம்",
        "view_annotated": "கண்டறியப்பட்ட தழும்புகளின் எல்லைக் கட்டங்கள் (Bounding Boxes)",
        "view_heatmap": "Grad-CAM கவனக் குவிய வண்ணப் படம்",
        "view_combined": "ஒருங்கிணைந்த அடுக்குக் காட்சி",
        "safety_disclaimer": (
            "முக்கிய அறிவிப்பு: RetinaGuard AI என்பது முதற்கட்ட பரிசோதனைக்கான AI முடிவு உதவி மென்பொருளாகும். "
            "இந்த முடிவு இறுதி மருத்துவ நோயறிதல் அல்ல, தகுதியான கண் மருத்துவரால உறுதி செய்யப்பட வேண்டும்."
        )
    },
    "hi": {
        "app_title": "रेटिनागार्ड AI - रेटिनोपैथी गंभीरता एवं लिसन विश्लेषण प्रणाली",
        "disclaimer_banner": "AI-सहायता प्राप्त प्रारंभिक स्क्रीनिंग उपकरण। यह नेत्र रोग विशेषज्ञ का विकल्प नहीं है और न ही अंतिम निदान है।",
        "nav_dashboard": "डैशबोर्ड",
        "nav_new_screening": "नई स्क्रीनिंग",
        "nav_history": "स्क्रीनिंग इतिहास",
        "quality_pass": "इमेज गुणवत्ता: विश्लेषण के लिए स्वीकार्य",
        "quality_fail": "इमेज गुणवत्ता: विश्वसनीय विश्लेषण के लिए अपर्याप्त",
        "recapture_title": "पुनः इमेज लेने हेतु मार्गदर्शन",
        "icdr_0": "कोई डायबिटिक रेटिनोपैथी नहीं (No Apparent DR - Grade 0)",
        "icdr_1": "हल्का NPDR (Mild NPDR - Grade 1)",
        "icdr_2": "मध्यम NPDR (Moderate NPDR - Grade 2)",
        "icdr_3": "गंभीर नॉन-प्रोलिफेरेटिव डायबेटिक रेटिनोपैथी (Severe NPDR - Grade 3)",
        "icdr_4": "प्रोलिफेरेटिव डायबेटिक रेटिनोपैथी (PDR - Grade 4)",
        "action_0": "AI मॉडल द्वारा कोई रेटिनोपैथी नहीं पाई गई। वार्षिक नियमित जांच जारी रखें।",
        "action_1": "रेटिना में हल्के बदलाव पाए गए हैं। 6 से 12 महीनों में डॉक्टर से परामर्श करें।",
        "action_2": "रेटिना में मध्यम बदलाव पाए गए हैं। 3 से 6 महीनों में नेत्र विशेषज्ञ से जांच करवाएं।",
        "action_3": "रेटिना में गंभीर बदलाव पाए गए हैं। 1 से 4 सप्ताह के भीतर शीघ्र नेत्र विशेषज्ञ से परामर्श लें।",
        "action_4": "अत्यधिक गंभीर प्रोलिफेरेटिव लक्षण पाए गए हैं। 1 से 2 सप्ताह में तत्काल विशेषज्ञ से मिलें।",
        "lesion_exudates": "हार्ड एक्सूडेट्स (वसा जमाव)",
        "lesion_hemorrhages": "रेटिनल रक्तस्राव (Hemorrhages)",
        "lesion_microaneurysms": "माइक्रोएन्यूरिज्म",
        "lesion_cws": "कॉटन-वूल स्पॉट्स",
        "view_original": "मूल रेटिना इमेज",
        "view_annotated": "चिह्नित लिसन बाउंडिंग बॉक्स (Bounding Boxes)",
        "view_heatmap": "Grad-CAM अटेंशन हीटमैप",
        "view_combined": "संयुक्त परत दृश्य",
        "safety_disclaimer": (
            "महत्वपूर्ण सूचना: RetinaGuard AI एक AI-सहायता प्राप्त निर्णय-सहायता सॉफ्टवेयर है। "
            "यह परिणाम अंतिम निदान नहीं है और एक योग्य नेत्र विशेषज्ञ द्वारा मूल्यांकित किया जाना चाहिए।"
        )
    }
}

def get_text(key: str, lang: str = "en") -> str:
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return lang_dict.get(key, TRANSLATIONS["en"].get(key, key))

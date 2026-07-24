# Casagrand RAG Knowledge Base

Approved knowledge used by the outbound voice agent for RAG retrieval.

| Item | Count |
|---|---:|
| Projects | 3 |
| FAQ cards | 90 |
| Escalation rules | 6 |
| Indexed RAG documents | 102 |
| Languages | English, Tamil, Tanglish |
| Source | Local seed + Hugging Face `Harir2002/casagrand_projects_faq` |

---

## Table of contents

1. [Project cards](#1-project-cards)
2. [FAQ cards](#2-faq-cards)
3. [Escalation rules](#3-escalation-rules)
4. [Indexed RAG documents](#4-indexed-rag-documents)

---

## 1. Project cards

### Casagrand Highcity (`highcity`)

- **City:** Chennai
- **Location:** Perumbakkam, Chennai
- **Status:** ready_to_move / under construction (demo)
- **Typology:** 2 & 3 BHK apartments
- **Pricing from:** INR 75 Lakh onwards (indicative demo)
- **Language:** en
- **Aliases:** highcity, high city, ஹைசிட்டி

**Amenities**

- clubhouse
- swimming pool
- gym
- children's play area
- landscaped gardens
- 24x7 security

**Highlights**

- Well-connected residential location in South Chennai
- Designed for family living with community amenities
- Site visits available by appointment

**Education**

Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living.

**Site visit note**

We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point.

**Brochure note**

I can arrange the Highcity brochure and share it after this call via the sales desk.

### Casagrand Avenuepark (`avenuepark`)

- **City:** Chennai
- **Location:** Tambaram / South Chennai corridor (demo)
- **Status:** upcoming / booking open (demo)
- **Typology:** 2 & 3 BHK apartments
- **Pricing from:** INR 65 Lakh onwards (indicative demo)
- **Language:** en
- **Aliases:** avenuepark, avenue park, avenue, அவென்யூ

**Amenities**

- clubhouse
- jogging track
- indoor games
- multipurpose hall
- CCTV surveillance

**Highlights**

- Focused on value and practical layouts
- Access to key southern transit nodes
- Amenities planned for everyday family use

**Education**

Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities.

**Site visit note**

Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window.

**Brochure note**

I can arrange the Avenuepark brochure through our advisor team.

### Casagrand Mercury (`mercury`)

- **City:** Chennai
- **Location:** OMR / IT corridor adjacency (demo)
- **Status:** launch / early booking (demo)
- **Typology:** premium 2 & 3 BHK apartments
- **Pricing from:** INR 90 Lakh onwards (indicative demo)
- **Language:** en
- **Aliases:** mercury, மெர்க்குரி, மெர்குரி

**Amenities**

- premium clubhouse
- infinity / leisure pool
- work-from-home lounge
- sky deck
- concierge desk (demo)

**Highlights**

- Designed for professionals along the IT corridor
- Premium finishes and elevated amenities (demo framing)
- Priority site visits for early registrants

**Education**

Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living.

**Site visit note**

Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk.

**Brochure note**

I can arrange the Mercury brochure for early registrants.

---

## 2. FAQ cards

Grouped by project, then language, then intent.

### Casagrand Highcity

#### Language: `en`

##### amenities — `highcity:amenities:en`

- **Category:** amenities
- **Source:** `projects@2026.07.15:highcity:amenities`
- **Question:** What amenities are available?

**Answer**

Casagrand Highcity amenities include: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security.

##### brochure — `highcity:brochure:en`

- **Category:** brochure
- **Source:** `projects@2026.07.15:highcity:brochure`
- **Question:** Please send the brochure

**Answer**

I can arrange the Highcity brochure and share it after this call via the sales desk. I've noted your request.

##### brochure_summary — `highcity:education:en`

- **Category:** brochure
- **Source:** `projects@2026.07.15:highcity:education`
- **Question:** brochure summary / project overview

**Answer**

Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. Would you like amenities, pricing, or location next?

##### callback — `highcity:callback:en`

- **Category:** callback
- **Source:** `projects@2026.07.15:highcity:callback`
- **Question:** Please arrange a callback

**Answer**

I'll arrange a callback about Casagrand Highcity. What time works best?

##### greeting — `highcity:greeting:en`

- **Category:** greeting
- **Source:** `projects@2026.07.15:highcity:introduction`
- **Question:** hello / vanakkam

**Answer**

Hello! I'm the Casagrand voice assistant. Today we can talk about Casagrand Highcity — amenities, location, pricing, and booking a site visit. May I continue?

##### location — `highcity:location:en`

- **Category:** location
- **Source:** `projects@2026.07.15:highcity:location`
- **Question:** Where is the project located?

**Answer**

Casagrand Highcity is located at Perumbakkam, Chennai (Chennai).

##### out_of_domain — `highcity:ood:en`

- **Category:** fallback
- **Source:** `projects@2026.07.15:highcity:safe_fallback`
- **Question:** out of domain

**Answer**

I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

##### pricing — `highcity:pricing:en`

- **Category:** pricing
- **Source:** `projects@2026.07.15:highcity:pricing`
- **Question:** What is the pricing?

**Answer**

Casagrand Highcity pricing starts at INR 75 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

##### project_info — `highcity:project_info:en`

- **Category:** project_info
- **Source:** `projects@2026.07.15:highcity:project_info`
- **Question:** Tell me about the project

**Answer**

Casagrand Highcity offers 2 & 3 BHK apartments at Perumbakkam, Chennai. Status: ready_to_move / under construction (demo). Highlights: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

##### site_visit — `highcity:site_visit:en`

- **Category:** site_visit
- **Source:** `projects@2026.07.15:highcity:site_visit`
- **Question:** Can I book a site visit?

**Answer**

We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point. Which day works for you?

#### Language: `ta`

##### amenities — `highcity:amenities:ta`

- **Category:** amenities
- **Source:** `projects@2026.07.15:highcity:amenities`
- **Question:** வசதிகள் என்ன?

**Answer**

Casagrand Highcity வசதிகள்: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security.

##### brochure — `highcity:brochure:ta`

- **Category:** brochure
- **Source:** `projects@2026.07.15:highcity:brochure`
- **Question:** brochure அனுப்புங்கள்

**Answer**

I can arrange the Highcity brochure and share it after this call via the sales desk. உங்கள் விருப்பத்தை பதிவு செய்தேன்.

##### brochure_summary — `highcity:education:ta`

- **Category:** brochure
- **Source:** `projects@2026.07.15:highcity:education`
- **Question:** brochure summary / project overview

**Answer**

Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?

##### callback — `highcity:callback:ta`

- **Category:** callback
- **Source:** `projects@2026.07.15:highcity:callback`
- **Question:** கால்பேக் ஏற்பாடு செய்யுங்கள்

**Answer**

Casagrand Highcity குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். விருப்பமான நேரம் சொல்லுங்கள்.

##### greeting — `highcity:greeting:ta`

- **Category:** greeting
- **Source:** `projects@2026.07.15:highcity:introduction`
- **Question:** hello / vanakkam

**Answer**

வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று Casagrand Highcity பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. தொடர அனுமதி இருக்கிறதா?

##### location — `highcity:location:ta`

- **Category:** location
- **Source:** `projects@2026.07.15:highcity:location`
- **Question:** இடம் எங்கே?

**Answer**

Casagrand Highcity இடம்: Perumbakkam, Chennai (Chennai).

##### out_of_domain — `highcity:ood:ta`

- **Category:** fallback
- **Source:** `projects@2026.07.15:highcity:safe_fallback`
- **Question:** out of domain

**Answer**

நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

##### pricing — `highcity:pricing:ta`

- **Category:** pricing
- **Source:** `projects@2026.07.15:highcity:pricing`
- **Question:** விலை என்ன?

**Answer**

Casagrand Highcity விலை: INR 75 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

##### project_info — `highcity:project_info:ta`

- **Category:** project_info
- **Source:** `projects@2026.07.15:highcity:project_info`
- **Question:** திட்டம் பற்றி சொல்லுங்கள்

**Answer**

Casagrand Highcity — 2 & 3 BHK apartments @ Perumbakkam, Chennai. நிலை: ready_to_move / under construction (demo). முக்கிய அம்சங்கள்: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

##### site_visit — `highcity:site_visit:ta`

- **Category:** site_visit
- **Source:** `projects@2026.07.15:highcity:site_visit`
- **Question:** தள வருகை புக் செய்யலாமா?

**Answer**

We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point. வசதியான நாள் சொல்லுங்கள்.

#### Language: `tanglish`

##### amenities — `highcity:amenities:tanglish`

- **Category:** amenities
- **Source:** `projects@2026.07.15:highcity:amenities`
- **Question:** amenities enna?

**Answer**

Casagrand Highcity amenities: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security.

##### brochure — `highcity:brochure:tanglish`

- **Category:** brochure
- **Source:** `projects@2026.07.15:highcity:brochure`
- **Question:** brochure anuppunga

**Answer**

I can arrange the Highcity brochure and share it after this call via the sales desk. Request register paniren.

##### brochure_summary — `highcity:education:tanglish`

- **Category:** brochure
- **Source:** `projects@2026.07.15:highcity:education`
- **Question:** brochure summary / project overview

**Answer**

Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. Innum details venuma — amenities, pricing, illa location?

##### callback — `highcity:callback:tanglish`

- **Category:** callback
- **Source:** `projects@2026.07.15:highcity:callback`
- **Question:** callback arrange pannunga

**Answer**

Casagrand Highcity pathi callback arrange panren. Preferred time sollunga.

##### greeting — `highcity:greeting:tanglish`

- **Category:** greeting
- **Source:** `projects@2026.07.15:highcity:introduction`
- **Question:** hello / vanakkam

**Answer**

Vanakkam! Naan Casagrand voice assistant. Indha call la Casagrand Highcity pathi discuss pannalam — amenities, location, pricing, site visit. Continue panna okay va?

##### location — `highcity:location:tanglish`

- **Category:** location
- **Source:** `projects@2026.07.15:highcity:location`
- **Question:** location enge?

**Answer**

Casagrand Highcity location: Perumbakkam, Chennai (Chennai).

##### out_of_domain — `highcity:ood:tanglish`

- **Category:** fallback
- **Source:** `projects@2026.07.15:highcity:safe_fallback`
- **Question:** out of domain

**Answer**

Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

##### pricing — `highcity:pricing:tanglish`

- **Category:** pricing
- **Source:** `projects@2026.07.15:highcity:pricing`
- **Question:** pricing evlo?

**Answer**

Casagrand Highcity pricing: INR 75 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

##### project_info — `highcity:project_info:tanglish`

- **Category:** project_info
- **Source:** `projects@2026.07.15:highcity:project_info`
- **Question:** project pathi sollunga

**Answer**

Casagrand Highcity — 2 & 3 BHK apartments @ Perumbakkam, Chennai. Status: ready_to_move / under construction (demo). Highlights: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

##### site_visit — `highcity:site_visit:tanglish`

- **Category:** site_visit
- **Source:** `projects@2026.07.15:highcity:site_visit`
- **Question:** site visit book pannalama?

**Answer**

We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point. Convenient day sollunga.

---

### Casagrand Avenuepark

#### Language: `en`

##### amenities — `avenuepark:amenities:en`

- **Category:** amenities
- **Source:** `projects@2026.07.15:avenuepark:amenities`
- **Question:** What amenities are available?

**Answer**

Casagrand Avenuepark amenities include: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance.

##### brochure — `avenuepark:brochure:en`

- **Category:** brochure
- **Source:** `projects@2026.07.15:avenuepark:brochure`
- **Question:** Please send the brochure

**Answer**

I can arrange the Avenuepark brochure through our advisor team. I've noted your request.

##### brochure_summary — `avenuepark:education:en`

- **Category:** brochure
- **Source:** `projects@2026.07.15:avenuepark:education`
- **Question:** brochure summary / project overview

**Answer**

Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. Would you like amenities, pricing, or location next?

##### callback — `avenuepark:callback:en`

- **Category:** callback
- **Source:** `projects@2026.07.15:avenuepark:callback`
- **Question:** Please arrange a callback

**Answer**

I'll arrange a callback about Casagrand Avenuepark. What time works best?

##### greeting — `avenuepark:greeting:en`

- **Category:** greeting
- **Source:** `projects@2026.07.15:avenuepark:introduction`
- **Question:** hello / vanakkam

**Answer**

Hello! I'm the Casagrand voice assistant. Today we can talk about Casagrand Avenuepark — amenities, location, pricing, and booking a site visit. May I continue?

##### location — `avenuepark:location:en`

- **Category:** location
- **Source:** `projects@2026.07.15:avenuepark:location`
- **Question:** Where is the project located?

**Answer**

Casagrand Avenuepark is located at Tambaram / South Chennai corridor (demo) (Chennai).

##### out_of_domain — `avenuepark:ood:en`

- **Category:** fallback
- **Source:** `projects@2026.07.15:avenuepark:safe_fallback`
- **Question:** out of domain

**Answer**

I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

##### pricing — `avenuepark:pricing:en`

- **Category:** pricing
- **Source:** `projects@2026.07.15:avenuepark:pricing`
- **Question:** What is the pricing?

**Answer**

Casagrand Avenuepark pricing starts at INR 65 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

##### project_info — `avenuepark:project_info:en`

- **Category:** project_info
- **Source:** `projects@2026.07.15:avenuepark:project_info`
- **Question:** Tell me about the project

**Answer**

Casagrand Avenuepark offers 2 & 3 BHK apartments at Tambaram / South Chennai corridor (demo). Status: upcoming / booking open (demo). Highlights: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

##### site_visit — `avenuepark:site_visit:en`

- **Category:** site_visit
- **Source:** `projects@2026.07.15:avenuepark:site_visit`
- **Question:** Can I book a site visit?

**Answer**

Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window. Which day works for you?

#### Language: `ta`

##### amenities — `avenuepark:amenities:ta`

- **Category:** amenities
- **Source:** `projects@2026.07.15:avenuepark:amenities`
- **Question:** வசதிகள் என்ன?

**Answer**

Casagrand Avenuepark வசதிகள்: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance.

##### brochure — `avenuepark:brochure:ta`

- **Category:** brochure
- **Source:** `projects@2026.07.15:avenuepark:brochure`
- **Question:** brochure அனுப்புங்கள்

**Answer**

I can arrange the Avenuepark brochure through our advisor team. உங்கள் விருப்பத்தை பதிவு செய்தேன்.

##### brochure_summary — `avenuepark:education:ta`

- **Category:** brochure
- **Source:** `projects@2026.07.15:avenuepark:education`
- **Question:** brochure summary / project overview

**Answer**

Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?

##### callback — `avenuepark:callback:ta`

- **Category:** callback
- **Source:** `projects@2026.07.15:avenuepark:callback`
- **Question:** கால்பேக் ஏற்பாடு செய்யுங்கள்

**Answer**

Casagrand Avenuepark குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். விருப்பமான நேரம் சொல்லுங்கள்.

##### greeting — `avenuepark:greeting:ta`

- **Category:** greeting
- **Source:** `projects@2026.07.15:avenuepark:introduction`
- **Question:** hello / vanakkam

**Answer**

வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று Casagrand Avenuepark பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. தொடர அனுமதி இருக்கிறதா?

##### location — `avenuepark:location:ta`

- **Category:** location
- **Source:** `projects@2026.07.15:avenuepark:location`
- **Question:** இடம் எங்கே?

**Answer**

Casagrand Avenuepark இடம்: Tambaram / South Chennai corridor (demo) (Chennai).

##### out_of_domain — `avenuepark:ood:ta`

- **Category:** fallback
- **Source:** `projects@2026.07.15:avenuepark:safe_fallback`
- **Question:** out of domain

**Answer**

நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

##### pricing — `avenuepark:pricing:ta`

- **Category:** pricing
- **Source:** `projects@2026.07.15:avenuepark:pricing`
- **Question:** விலை என்ன?

**Answer**

Casagrand Avenuepark விலை: INR 65 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

##### project_info — `avenuepark:project_info:ta`

- **Category:** project_info
- **Source:** `projects@2026.07.15:avenuepark:project_info`
- **Question:** திட்டம் பற்றி சொல்லுங்கள்

**Answer**

Casagrand Avenuepark — 2 & 3 BHK apartments @ Tambaram / South Chennai corridor (demo). நிலை: upcoming / booking open (demo). முக்கிய அம்சங்கள்: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

##### site_visit — `avenuepark:site_visit:ta`

- **Category:** site_visit
- **Source:** `projects@2026.07.15:avenuepark:site_visit`
- **Question:** தள வருகை புக் செய்யலாமா?

**Answer**

Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window. வசதியான நாள் சொல்லுங்கள்.

#### Language: `tanglish`

##### amenities — `avenuepark:amenities:tanglish`

- **Category:** amenities
- **Source:** `projects@2026.07.15:avenuepark:amenities`
- **Question:** amenities enna?

**Answer**

Casagrand Avenuepark amenities: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance.

##### brochure — `avenuepark:brochure:tanglish`

- **Category:** brochure
- **Source:** `projects@2026.07.15:avenuepark:brochure`
- **Question:** brochure anuppunga

**Answer**

I can arrange the Avenuepark brochure through our advisor team. Request register paniren.

##### brochure_summary — `avenuepark:education:tanglish`

- **Category:** brochure
- **Source:** `projects@2026.07.15:avenuepark:education`
- **Question:** brochure summary / project overview

**Answer**

Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. Innum details venuma — amenities, pricing, illa location?

##### callback — `avenuepark:callback:tanglish`

- **Category:** callback
- **Source:** `projects@2026.07.15:avenuepark:callback`
- **Question:** callback arrange pannunga

**Answer**

Casagrand Avenuepark pathi callback arrange panren. Preferred time sollunga.

##### greeting — `avenuepark:greeting:tanglish`

- **Category:** greeting
- **Source:** `projects@2026.07.15:avenuepark:introduction`
- **Question:** hello / vanakkam

**Answer**

Vanakkam! Naan Casagrand voice assistant. Indha call la Casagrand Avenuepark pathi discuss pannalam — amenities, location, pricing, site visit. Continue panna okay va?

##### location — `avenuepark:location:tanglish`

- **Category:** location
- **Source:** `projects@2026.07.15:avenuepark:location`
- **Question:** location enge?

**Answer**

Casagrand Avenuepark location: Tambaram / South Chennai corridor (demo) (Chennai).

##### out_of_domain — `avenuepark:ood:tanglish`

- **Category:** fallback
- **Source:** `projects@2026.07.15:avenuepark:safe_fallback`
- **Question:** out of domain

**Answer**

Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

##### pricing — `avenuepark:pricing:tanglish`

- **Category:** pricing
- **Source:** `projects@2026.07.15:avenuepark:pricing`
- **Question:** pricing evlo?

**Answer**

Casagrand Avenuepark pricing: INR 65 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

##### project_info — `avenuepark:project_info:tanglish`

- **Category:** project_info
- **Source:** `projects@2026.07.15:avenuepark:project_info`
- **Question:** project pathi sollunga

**Answer**

Casagrand Avenuepark — 2 & 3 BHK apartments @ Tambaram / South Chennai corridor (demo). Status: upcoming / booking open (demo). Highlights: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

##### site_visit — `avenuepark:site_visit:tanglish`

- **Category:** site_visit
- **Source:** `projects@2026.07.15:avenuepark:site_visit`
- **Question:** site visit book pannalama?

**Answer**

Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window. Convenient day sollunga.

---

### Casagrand Mercury

#### Language: `en`

##### amenities — `mercury:amenities:en`

- **Category:** amenities
- **Source:** `projects@2026.07.15:mercury:amenities`
- **Question:** What amenities are available?

**Answer**

Casagrand Mercury amenities include: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo).

##### brochure — `mercury:brochure:en`

- **Category:** brochure
- **Source:** `projects@2026.07.15:mercury:brochure`
- **Question:** Please send the brochure

**Answer**

I can arrange the Mercury brochure for early registrants. I've noted your request.

##### brochure_summary — `mercury:education:en`

- **Category:** brochure
- **Source:** `projects@2026.07.15:mercury:education`
- **Question:** brochure summary / project overview

**Answer**

Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. Would you like amenities, pricing, or location next?

##### callback — `mercury:callback:en`

- **Category:** callback
- **Source:** `projects@2026.07.15:mercury:callback`
- **Question:** Please arrange a callback

**Answer**

I'll arrange a callback about Casagrand Mercury. What time works best?

##### greeting — `mercury:greeting:en`

- **Category:** greeting
- **Source:** `projects@2026.07.15:mercury:introduction`
- **Question:** hello / vanakkam

**Answer**

Hello! I'm the Casagrand voice assistant. Today we can talk about Casagrand Mercury — amenities, location, pricing, and booking a site visit. May I continue?

##### location — `mercury:location:en`

- **Category:** location
- **Source:** `projects@2026.07.15:mercury:location`
- **Question:** Where is the project located?

**Answer**

Casagrand Mercury is located at OMR / IT corridor adjacency (demo) (Chennai).

##### out_of_domain — `mercury:ood:en`

- **Category:** fallback
- **Source:** `projects@2026.07.15:mercury:safe_fallback`
- **Question:** out of domain

**Answer**

I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

##### pricing — `mercury:pricing:en`

- **Category:** pricing
- **Source:** `projects@2026.07.15:mercury:pricing`
- **Question:** What is the pricing?

**Answer**

Casagrand Mercury pricing starts at INR 90 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

##### project_info — `mercury:project_info:en`

- **Category:** project_info
- **Source:** `projects@2026.07.15:mercury:project_info`
- **Question:** Tell me about the project

**Answer**

Casagrand Mercury offers premium 2 & 3 BHK apartments at OMR / IT corridor adjacency (demo). Status: launch / early booking (demo). Highlights: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

##### site_visit — `mercury:site_visit:en`

- **Category:** site_visit
- **Source:** `projects@2026.07.15:mercury:site_visit`
- **Question:** Can I book a site visit?

**Answer**

Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk. Which day works for you?

#### Language: `ta`

##### amenities — `mercury:amenities:ta`

- **Category:** amenities
- **Source:** `projects@2026.07.15:mercury:amenities`
- **Question:** வசதிகள் என்ன?

**Answer**

Casagrand Mercury வசதிகள்: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo).

##### brochure — `mercury:brochure:ta`

- **Category:** brochure
- **Source:** `projects@2026.07.15:mercury:brochure`
- **Question:** brochure அனுப்புங்கள்

**Answer**

I can arrange the Mercury brochure for early registrants. உங்கள் விருப்பத்தை பதிவு செய்தேன்.

##### brochure_summary — `mercury:education:ta`

- **Category:** brochure
- **Source:** `projects@2026.07.15:mercury:education`
- **Question:** brochure summary / project overview

**Answer**

Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?

##### callback — `mercury:callback:ta`

- **Category:** callback
- **Source:** `projects@2026.07.15:mercury:callback`
- **Question:** கால்பேக் ஏற்பாடு செய்யுங்கள்

**Answer**

Casagrand Mercury குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். விருப்பமான நேரம் சொல்லுங்கள்.

##### greeting — `mercury:greeting:ta`

- **Category:** greeting
- **Source:** `projects@2026.07.15:mercury:introduction`
- **Question:** hello / vanakkam

**Answer**

வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று Casagrand Mercury பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. தொடர அனுமதி இருக்கிறதா?

##### location — `mercury:location:ta`

- **Category:** location
- **Source:** `projects@2026.07.15:mercury:location`
- **Question:** இடம் எங்கே?

**Answer**

Casagrand Mercury இடம்: OMR / IT corridor adjacency (demo) (Chennai).

##### out_of_domain — `mercury:ood:ta`

- **Category:** fallback
- **Source:** `projects@2026.07.15:mercury:safe_fallback`
- **Question:** out of domain

**Answer**

நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

##### pricing — `mercury:pricing:ta`

- **Category:** pricing
- **Source:** `projects@2026.07.15:mercury:pricing`
- **Question:** விலை என்ன?

**Answer**

Casagrand Mercury விலை: INR 90 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

##### project_info — `mercury:project_info:ta`

- **Category:** project_info
- **Source:** `projects@2026.07.15:mercury:project_info`
- **Question:** திட்டம் பற்றி சொல்லுங்கள்

**Answer**

Casagrand Mercury — premium 2 & 3 BHK apartments @ OMR / IT corridor adjacency (demo). நிலை: launch / early booking (demo). முக்கிய அம்சங்கள்: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

##### site_visit — `mercury:site_visit:ta`

- **Category:** site_visit
- **Source:** `projects@2026.07.15:mercury:site_visit`
- **Question:** தள வருகை புக் செய்யலாமா?

**Answer**

Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk. வசதியான நாள் சொல்லுங்கள்.

#### Language: `tanglish`

##### amenities — `mercury:amenities:tanglish`

- **Category:** amenities
- **Source:** `projects@2026.07.15:mercury:amenities`
- **Question:** amenities enna?

**Answer**

Casagrand Mercury amenities: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo).

##### brochure — `mercury:brochure:tanglish`

- **Category:** brochure
- **Source:** `projects@2026.07.15:mercury:brochure`
- **Question:** brochure anuppunga

**Answer**

I can arrange the Mercury brochure for early registrants. Request register paniren.

##### brochure_summary — `mercury:education:tanglish`

- **Category:** brochure
- **Source:** `projects@2026.07.15:mercury:education`
- **Question:** brochure summary / project overview

**Answer**

Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. Innum details venuma — amenities, pricing, illa location?

##### callback — `mercury:callback:tanglish`

- **Category:** callback
- **Source:** `projects@2026.07.15:mercury:callback`
- **Question:** callback arrange pannunga

**Answer**

Casagrand Mercury pathi callback arrange panren. Preferred time sollunga.

##### greeting — `mercury:greeting:tanglish`

- **Category:** greeting
- **Source:** `projects@2026.07.15:mercury:introduction`
- **Question:** hello / vanakkam

**Answer**

Vanakkam! Naan Casagrand voice assistant. Indha call la Casagrand Mercury pathi discuss pannalam — amenities, location, pricing, site visit. Continue panna okay va?

##### location — `mercury:location:tanglish`

- **Category:** location
- **Source:** `projects@2026.07.15:mercury:location`
- **Question:** location enge?

**Answer**

Casagrand Mercury location: OMR / IT corridor adjacency (demo) (Chennai).

##### out_of_domain — `mercury:ood:tanglish`

- **Category:** fallback
- **Source:** `projects@2026.07.15:mercury:safe_fallback`
- **Question:** out of domain

**Answer**

Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

##### pricing — `mercury:pricing:tanglish`

- **Category:** pricing
- **Source:** `projects@2026.07.15:mercury:pricing`
- **Question:** pricing evlo?

**Answer**

Casagrand Mercury pricing: INR 90 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

##### project_info — `mercury:project_info:tanglish`

- **Category:** project_info
- **Source:** `projects@2026.07.15:mercury:project_info`
- **Question:** project pathi sollunga

**Answer**

Casagrand Mercury — premium 2 & 3 BHK apartments @ OMR / IT corridor adjacency (demo). Status: launch / early booking (demo). Highlights: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

##### site_visit — `mercury:site_visit:tanglish`

- **Category:** site_visit
- **Source:** `projects@2026.07.15:mercury:site_visit`
- **Question:** site visit book pannalama?

**Answer**

Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk. Convenient day sollunga.

---

## 3. Escalation rules

### `handoff:en`

- **Trigger:** human_handoff
- **Action:** handoff
- **Language:** en
- **Reason:** caller_requested_human

**Message**

Sure — I'll arrange a human handoff. A Casagrand advisor will continue from here. Please stay on the line.

### `ood_escalation:en`

- **Trigger:** out_of_domain
- **Action:** safe_fallback
- **Language:** en
- **Reason:** out_of_domain_topic

**Message**

I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

### `handoff:ta`

- **Trigger:** human_handoff
- **Action:** handoff
- **Language:** ta
- **Reason:** caller_requested_human

**Message**

சரி — மனித ஆலோசகருக்கு இணைக்கிறேன். Casagrand ஆலோசகர் தொடர்ந்து உதவுவார். தயவுசெய்து காத்திருக்கவும்.

### `ood_escalation:ta`

- **Trigger:** out_of_domain
- **Action:** safe_fallback
- **Language:** ta
- **Reason:** out_of_domain_topic

**Message**

நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

### `handoff:tanglish`

- **Trigger:** human_handoff
- **Action:** handoff
- **Language:** tanglish
- **Reason:** caller_requested_human

**Message**

Sure — human advisor ku connect panren. Casagrand advisor continue pannuvaanga. Please wait pannunga.

### `ood_escalation:tanglish`

- **Trigger:** out_of_domain
- **Action:** safe_fallback
- **Language:** tanglish
- **Reason:** out_of_domain_topic

**Message**

Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

---

## 4. Indexed RAG documents

These are the chunks placed into the vector/memory index at startup.

### Record type: `project` (3)

#### `project:highcity:brochure`

- **Project:** highcity
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** en
- **Title:** Casagrand Highcity brochure
- **Metadata:** name=Casagrand Highcity, source=projects@2026.07.15

**Text**

Casagrand Highcity. Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. Location: Perumbakkam, Chennai. Typology: 2 & 3 BHK apartments. Pricing: INR 75 Lakh onwards (indicative demo). Amenities: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security. Highlights: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

#### `project:avenuepark:brochure`

- **Project:** avenuepark
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** en
- **Title:** Casagrand Avenuepark brochure
- **Metadata:** name=Casagrand Avenuepark, source=projects@2026.07.15

**Text**

Casagrand Avenuepark. Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. Location: Tambaram / South Chennai corridor (demo). Typology: 2 & 3 BHK apartments. Pricing: INR 65 Lakh onwards (indicative demo). Amenities: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance. Highlights: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

#### `project:mercury:brochure`

- **Project:** mercury
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** en
- **Title:** Casagrand Mercury brochure
- **Metadata:** name=Casagrand Mercury, source=projects@2026.07.15

**Text**

Casagrand Mercury. Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. Location: OMR / IT corridor adjacency (demo). Typology: premium 2 & 3 BHK apartments. Pricing: INR 90 Lakh onwards (indicative demo). Amenities: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo). Highlights: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

### Record type: `comparison` (3)

#### `project:highcity:comparison`

- **Project:** highcity
- **Intent:** comparison
- **Category:** comparison
- **Language:** en
- **Title:** Casagrand Highcity comparison card
- **Metadata:** name=Casagrand Highcity, pricing_from=INR 75 Lakh onwards (indicative demo)

**Text**

Compare Casagrand Highcity: 2 & 3 BHK apartments at Perumbakkam, Chennai, status ready_to_move / under construction (demo), from INR 75 Lakh onwards (indicative demo).

#### `project:avenuepark:comparison`

- **Project:** avenuepark
- **Intent:** comparison
- **Category:** comparison
- **Language:** en
- **Title:** Casagrand Avenuepark comparison card
- **Metadata:** name=Casagrand Avenuepark, pricing_from=INR 65 Lakh onwards (indicative demo)

**Text**

Compare Casagrand Avenuepark: 2 & 3 BHK apartments at Tambaram / South Chennai corridor (demo), status upcoming / booking open (demo), from INR 65 Lakh onwards (indicative demo).

#### `project:mercury:comparison`

- **Project:** mercury
- **Intent:** comparison
- **Category:** comparison
- **Language:** en
- **Title:** Casagrand Mercury comparison card
- **Metadata:** name=Casagrand Mercury, pricing_from=INR 90 Lakh onwards (indicative demo)

**Text**

Compare Casagrand Mercury: premium 2 & 3 BHK apartments at OMR / IT corridor adjacency (demo), status launch / early booking (demo), from INR 90 Lakh onwards (indicative demo).

### Record type: `faq` (90)

#### `faq:highcity:project_info:en`

- **Project:** highcity
- **Intent:** project_info
- **Category:** project_info
- **Language:** en
- **Title:** Tell me about the project
- **Metadata:** source=projects@2026.07.15:highcity:project_info, answer=Casagrand Highcity offers 2 & 3 BHK apartments at Perumbakkam, Chennai. Status: ready_to_move / under construction (demo). Highlights: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

**Text**

Q: Tell me about the project
A: Casagrand Highcity offers 2 & 3 BHK apartments at Perumbakkam, Chennai. Status: ready_to_move / under construction (demo). Highlights: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

#### `faq:highcity:pricing:en`

- **Project:** highcity
- **Intent:** pricing
- **Category:** pricing
- **Language:** en
- **Title:** What is the pricing?
- **Metadata:** source=projects@2026.07.15:highcity:pricing, answer=Casagrand Highcity pricing starts at INR 75 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

**Text**

Q: What is the pricing?
A: Casagrand Highcity pricing starts at INR 75 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

#### `faq:highcity:location:en`

- **Project:** highcity
- **Intent:** location
- **Category:** location
- **Language:** en
- **Title:** Where is the project located?
- **Metadata:** source=projects@2026.07.15:highcity:location, answer=Casagrand Highcity is located at Perumbakkam, Chennai (Chennai).

**Text**

Q: Where is the project located?
A: Casagrand Highcity is located at Perumbakkam, Chennai (Chennai).

#### `faq:highcity:amenities:en`

- **Project:** highcity
- **Intent:** amenities
- **Category:** amenities
- **Language:** en
- **Title:** What amenities are available?
- **Metadata:** source=projects@2026.07.15:highcity:amenities, answer=Casagrand Highcity amenities include: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security.

**Text**

Q: What amenities are available?
A: Casagrand Highcity amenities include: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security.

#### `faq:highcity:site_visit:en`

- **Project:** highcity
- **Intent:** site_visit
- **Category:** site_visit
- **Language:** en
- **Title:** Can I book a site visit?
- **Metadata:** source=projects@2026.07.15:highcity:site_visit, answer=We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point. Which day works for you?

**Text**

Q: Can I book a site visit?
A: We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point. Which day works for you?

#### `faq:highcity:callback:en`

- **Project:** highcity
- **Intent:** callback
- **Category:** callback
- **Language:** en
- **Title:** Please arrange a callback
- **Metadata:** source=projects@2026.07.15:highcity:callback, answer=I'll arrange a callback about Casagrand Highcity. What time works best?

**Text**

Q: Please arrange a callback
A: I'll arrange a callback about Casagrand Highcity. What time works best?

#### `faq:highcity:brochure:en`

- **Project:** highcity
- **Intent:** brochure
- **Category:** brochure
- **Language:** en
- **Title:** Please send the brochure
- **Metadata:** source=projects@2026.07.15:highcity:brochure, answer=I can arrange the Highcity brochure and share it after this call via the sales desk. I've noted your request.

**Text**

Q: Please send the brochure
A: I can arrange the Highcity brochure and share it after this call via the sales desk. I've noted your request.

#### `faq:highcity:greeting:en`

- **Project:** highcity
- **Intent:** greeting
- **Category:** greeting
- **Language:** en
- **Title:** hello / vanakkam
- **Metadata:** source=projects@2026.07.15:highcity:introduction, answer=Hello! I'm the Casagrand voice assistant. Today we can talk about Casagrand Highcity — amenities, location, pricing, and booking a site visit. May I continue?

**Text**

Q: hello / vanakkam
A: Hello! I'm the Casagrand voice assistant. Today we can talk about Casagrand Highcity — amenities, location, pricing, and booking a site visit. May I continue?

#### `faq:highcity:education:en`

- **Project:** highcity
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** en
- **Title:** brochure summary / project overview
- **Metadata:** source=projects@2026.07.15:highcity:education, answer=Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. Would you like amenities, pricing, or location next?

**Text**

Q: brochure summary / project overview
A: Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. Would you like amenities, pricing, or location next?

#### `faq:highcity:ood:en`

- **Project:** highcity
- **Intent:** out_of_domain
- **Category:** fallback
- **Language:** en
- **Title:** out of domain
- **Metadata:** source=projects@2026.07.15:highcity:safe_fallback, answer=I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

**Text**

Q: out of domain
A: I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

#### `faq:highcity:project_info:ta`

- **Project:** highcity
- **Intent:** project_info
- **Category:** project_info
- **Language:** ta
- **Title:** திட்டம் பற்றி சொல்லுங்கள்
- **Metadata:** source=projects@2026.07.15:highcity:project_info, answer=Casagrand Highcity — 2 & 3 BHK apartments @ Perumbakkam, Chennai. நிலை: ready_to_move / under construction (demo). முக்கிய அம்சங்கள்: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

**Text**

Q: திட்டம் பற்றி சொல்லுங்கள்
A: Casagrand Highcity — 2 & 3 BHK apartments @ Perumbakkam, Chennai. நிலை: ready_to_move / under construction (demo). முக்கிய அம்சங்கள்: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

#### `faq:highcity:pricing:ta`

- **Project:** highcity
- **Intent:** pricing
- **Category:** pricing
- **Language:** ta
- **Title:** விலை என்ன?
- **Metadata:** source=projects@2026.07.15:highcity:pricing, answer=Casagrand Highcity விலை: INR 75 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

**Text**

Q: விலை என்ன?
A: Casagrand Highcity விலை: INR 75 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

#### `faq:highcity:location:ta`

- **Project:** highcity
- **Intent:** location
- **Category:** location
- **Language:** ta
- **Title:** இடம் எங்கே?
- **Metadata:** source=projects@2026.07.15:highcity:location, answer=Casagrand Highcity இடம்: Perumbakkam, Chennai (Chennai).

**Text**

Q: இடம் எங்கே?
A: Casagrand Highcity இடம்: Perumbakkam, Chennai (Chennai).

#### `faq:highcity:amenities:ta`

- **Project:** highcity
- **Intent:** amenities
- **Category:** amenities
- **Language:** ta
- **Title:** வசதிகள் என்ன?
- **Metadata:** source=projects@2026.07.15:highcity:amenities, answer=Casagrand Highcity வசதிகள்: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security.

**Text**

Q: வசதிகள் என்ன?
A: Casagrand Highcity வசதிகள்: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security.

#### `faq:highcity:site_visit:ta`

- **Project:** highcity
- **Intent:** site_visit
- **Category:** site_visit
- **Language:** ta
- **Title:** தள வருகை புக் செய்யலாமா?
- **Metadata:** source=projects@2026.07.15:highcity:site_visit, answer=We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point. வசதியான நாள் சொல்லுங்கள்.

**Text**

Q: தள வருகை புக் செய்யலாமா?
A: We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point. வசதியான நாள் சொல்லுங்கள்.

#### `faq:highcity:callback:ta`

- **Project:** highcity
- **Intent:** callback
- **Category:** callback
- **Language:** ta
- **Title:** கால்பேக் ஏற்பாடு செய்யுங்கள்
- **Metadata:** source=projects@2026.07.15:highcity:callback, answer=Casagrand Highcity குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். விருப்பமான நேரம் சொல்லுங்கள்.

**Text**

Q: கால்பேக் ஏற்பாடு செய்யுங்கள்
A: Casagrand Highcity குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். விருப்பமான நேரம் சொல்லுங்கள்.

#### `faq:highcity:brochure:ta`

- **Project:** highcity
- **Intent:** brochure
- **Category:** brochure
- **Language:** ta
- **Title:** brochure அனுப்புங்கள்
- **Metadata:** source=projects@2026.07.15:highcity:brochure, answer=I can arrange the Highcity brochure and share it after this call via the sales desk. உங்கள் விருப்பத்தை பதிவு செய்தேன்.

**Text**

Q: brochure அனுப்புங்கள்
A: I can arrange the Highcity brochure and share it after this call via the sales desk. உங்கள் விருப்பத்தை பதிவு செய்தேன்.

#### `faq:highcity:greeting:ta`

- **Project:** highcity
- **Intent:** greeting
- **Category:** greeting
- **Language:** ta
- **Title:** hello / vanakkam
- **Metadata:** source=projects@2026.07.15:highcity:introduction, answer=வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று Casagrand Highcity பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. தொடர அனுமதி இருக்கிறதா?

**Text**

Q: hello / vanakkam
A: வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று Casagrand Highcity பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. தொடர அனுமதி இருக்கிறதா?

#### `faq:highcity:education:ta`

- **Project:** highcity
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** ta
- **Title:** brochure summary / project overview
- **Metadata:** source=projects@2026.07.15:highcity:education, answer=Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?

**Text**

Q: brochure summary / project overview
A: Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?

#### `faq:highcity:ood:ta`

- **Project:** highcity
- **Intent:** out_of_domain
- **Category:** fallback
- **Language:** ta
- **Title:** out of domain
- **Metadata:** source=projects@2026.07.15:highcity:safe_fallback, answer=நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

**Text**

Q: out of domain
A: நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

#### `faq:highcity:project_info:tanglish`

- **Project:** highcity
- **Intent:** project_info
- **Category:** project_info
- **Language:** tanglish
- **Title:** project pathi sollunga
- **Metadata:** source=projects@2026.07.15:highcity:project_info, answer=Casagrand Highcity — 2 & 3 BHK apartments @ Perumbakkam, Chennai. Status: ready_to_move / under construction (demo). Highlights: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

**Text**

Q: project pathi sollunga
A: Casagrand Highcity — 2 & 3 BHK apartments @ Perumbakkam, Chennai. Status: ready_to_move / under construction (demo). Highlights: Well-connected residential location in South Chennai; Designed for family living with community amenities; Site visits available by appointment.

#### `faq:highcity:pricing:tanglish`

- **Project:** highcity
- **Intent:** pricing
- **Category:** pricing
- **Language:** tanglish
- **Title:** pricing evlo?
- **Metadata:** source=projects@2026.07.15:highcity:pricing, answer=Casagrand Highcity pricing: INR 75 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

**Text**

Q: pricing evlo?
A: Casagrand Highcity pricing: INR 75 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

#### `faq:highcity:location:tanglish`

- **Project:** highcity
- **Intent:** location
- **Category:** location
- **Language:** tanglish
- **Title:** location enge?
- **Metadata:** source=projects@2026.07.15:highcity:location, answer=Casagrand Highcity location: Perumbakkam, Chennai (Chennai).

**Text**

Q: location enge?
A: Casagrand Highcity location: Perumbakkam, Chennai (Chennai).

#### `faq:highcity:amenities:tanglish`

- **Project:** highcity
- **Intent:** amenities
- **Category:** amenities
- **Language:** tanglish
- **Title:** amenities enna?
- **Metadata:** source=projects@2026.07.15:highcity:amenities, answer=Casagrand Highcity amenities: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security.

**Text**

Q: amenities enna?
A: Casagrand Highcity amenities: clubhouse, swimming pool, gym, children's play area, landscaped gardens, 24x7 security.

#### `faq:highcity:site_visit:tanglish`

- **Project:** highcity
- **Intent:** site_visit
- **Category:** site_visit
- **Language:** tanglish
- **Title:** site visit book pannalama?
- **Metadata:** source=projects@2026.07.15:highcity:site_visit, answer=We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point. Convenient day sollunga.

**Text**

Q: site visit book pannalama?
A: We can book a guided site visit for Highcity. A relationship manager will confirm slot and meeting point. Convenient day sollunga.

#### `faq:highcity:callback:tanglish`

- **Project:** highcity
- **Intent:** callback
- **Category:** callback
- **Language:** tanglish
- **Title:** callback arrange pannunga
- **Metadata:** source=projects@2026.07.15:highcity:callback, answer=Casagrand Highcity pathi callback arrange panren. Preferred time sollunga.

**Text**

Q: callback arrange pannunga
A: Casagrand Highcity pathi callback arrange panren. Preferred time sollunga.

#### `faq:highcity:brochure:tanglish`

- **Project:** highcity
- **Intent:** brochure
- **Category:** brochure
- **Language:** tanglish
- **Title:** brochure anuppunga
- **Metadata:** source=projects@2026.07.15:highcity:brochure, answer=I can arrange the Highcity brochure and share it after this call via the sales desk. Request register paniren.

**Text**

Q: brochure anuppunga
A: I can arrange the Highcity brochure and share it after this call via the sales desk. Request register paniren.

#### `faq:highcity:greeting:tanglish`

- **Project:** highcity
- **Intent:** greeting
- **Category:** greeting
- **Language:** tanglish
- **Title:** hello / vanakkam
- **Metadata:** source=projects@2026.07.15:highcity:introduction, answer=Vanakkam! Naan Casagrand voice assistant. Indha call la Casagrand Highcity pathi discuss pannalam — amenities, location, pricing, site visit. Continue panna okay va?

**Text**

Q: hello / vanakkam
A: Vanakkam! Naan Casagrand voice assistant. Indha call la Casagrand Highcity pathi discuss pannalam — amenities, location, pricing, site visit. Continue panna okay va?

#### `faq:highcity:education:tanglish`

- **Project:** highcity
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** tanglish
- **Title:** brochure summary / project overview
- **Metadata:** source=projects@2026.07.15:highcity:education, answer=Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. Innum details venuma — amenities, pricing, illa location?

**Text**

Q: brochure summary / project overview
A: Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with clubhouse, pool, gym, and landscaped open spaces. It is suited for buyers looking at South Chennai connectivity and community living. Innum details venuma — amenities, pricing, illa location?

#### `faq:highcity:ood:tanglish`

- **Project:** highcity
- **Intent:** out_of_domain
- **Category:** fallback
- **Language:** tanglish
- **Title:** out of domain
- **Metadata:** source=projects@2026.07.15:highcity:safe_fallback, answer=Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

**Text**

Q: out of domain
A: Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

#### `faq:avenuepark:project_info:en`

- **Project:** avenuepark
- **Intent:** project_info
- **Category:** project_info
- **Language:** en
- **Title:** Tell me about the project
- **Metadata:** source=projects@2026.07.15:avenuepark:project_info, answer=Casagrand Avenuepark offers 2 & 3 BHK apartments at Tambaram / South Chennai corridor (demo). Status: upcoming / booking open (demo). Highlights: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

**Text**

Q: Tell me about the project
A: Casagrand Avenuepark offers 2 & 3 BHK apartments at Tambaram / South Chennai corridor (demo). Status: upcoming / booking open (demo). Highlights: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

#### `faq:avenuepark:pricing:en`

- **Project:** avenuepark
- **Intent:** pricing
- **Category:** pricing
- **Language:** en
- **Title:** What is the pricing?
- **Metadata:** source=projects@2026.07.15:avenuepark:pricing, answer=Casagrand Avenuepark pricing starts at INR 65 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

**Text**

Q: What is the pricing?
A: Casagrand Avenuepark pricing starts at INR 65 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

#### `faq:avenuepark:location:en`

- **Project:** avenuepark
- **Intent:** location
- **Category:** location
- **Language:** en
- **Title:** Where is the project located?
- **Metadata:** source=projects@2026.07.15:avenuepark:location, answer=Casagrand Avenuepark is located at Tambaram / South Chennai corridor (demo) (Chennai).

**Text**

Q: Where is the project located?
A: Casagrand Avenuepark is located at Tambaram / South Chennai corridor (demo) (Chennai).

#### `faq:avenuepark:amenities:en`

- **Project:** avenuepark
- **Intent:** amenities
- **Category:** amenities
- **Language:** en
- **Title:** What amenities are available?
- **Metadata:** source=projects@2026.07.15:avenuepark:amenities, answer=Casagrand Avenuepark amenities include: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance.

**Text**

Q: What amenities are available?
A: Casagrand Avenuepark amenities include: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance.

#### `faq:avenuepark:site_visit:en`

- **Project:** avenuepark
- **Intent:** site_visit
- **Category:** site_visit
- **Language:** en
- **Title:** Can I book a site visit?
- **Metadata:** source=projects@2026.07.15:avenuepark:site_visit, answer=Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window. Which day works for you?

**Text**

Q: Can I book a site visit?
A: Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window. Which day works for you?

#### `faq:avenuepark:callback:en`

- **Project:** avenuepark
- **Intent:** callback
- **Category:** callback
- **Language:** en
- **Title:** Please arrange a callback
- **Metadata:** source=projects@2026.07.15:avenuepark:callback, answer=I'll arrange a callback about Casagrand Avenuepark. What time works best?

**Text**

Q: Please arrange a callback
A: I'll arrange a callback about Casagrand Avenuepark. What time works best?

#### `faq:avenuepark:brochure:en`

- **Project:** avenuepark
- **Intent:** brochure
- **Category:** brochure
- **Language:** en
- **Title:** Please send the brochure
- **Metadata:** source=projects@2026.07.15:avenuepark:brochure, answer=I can arrange the Avenuepark brochure through our advisor team. I've noted your request.

**Text**

Q: Please send the brochure
A: I can arrange the Avenuepark brochure through our advisor team. I've noted your request.

#### `faq:avenuepark:greeting:en`

- **Project:** avenuepark
- **Intent:** greeting
- **Category:** greeting
- **Language:** en
- **Title:** hello / vanakkam
- **Metadata:** source=projects@2026.07.15:avenuepark:introduction, answer=Hello! I'm the Casagrand voice assistant. Today we can talk about Casagrand Avenuepark — amenities, location, pricing, and booking a site visit. May I continue?

**Text**

Q: hello / vanakkam
A: Hello! I'm the Casagrand voice assistant. Today we can talk about Casagrand Avenuepark — amenities, location, pricing, and booking a site visit. May I continue?

#### `faq:avenuepark:education:en`

- **Project:** avenuepark
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** en
- **Title:** brochure summary / project overview
- **Metadata:** source=projects@2026.07.15:avenuepark:education, answer=Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. Would you like amenities, pricing, or location next?

**Text**

Q: brochure summary / project overview
A: Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. Would you like amenities, pricing, or location next?

#### `faq:avenuepark:ood:en`

- **Project:** avenuepark
- **Intent:** out_of_domain
- **Category:** fallback
- **Language:** en
- **Title:** out of domain
- **Metadata:** source=projects@2026.07.15:avenuepark:safe_fallback, answer=I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

**Text**

Q: out of domain
A: I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

#### `faq:avenuepark:project_info:ta`

- **Project:** avenuepark
- **Intent:** project_info
- **Category:** project_info
- **Language:** ta
- **Title:** திட்டம் பற்றி சொல்லுங்கள்
- **Metadata:** source=projects@2026.07.15:avenuepark:project_info, answer=Casagrand Avenuepark — 2 & 3 BHK apartments @ Tambaram / South Chennai corridor (demo). நிலை: upcoming / booking open (demo). முக்கிய அம்சங்கள்: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

**Text**

Q: திட்டம் பற்றி சொல்லுங்கள்
A: Casagrand Avenuepark — 2 & 3 BHK apartments @ Tambaram / South Chennai corridor (demo). நிலை: upcoming / booking open (demo). முக்கிய அம்சங்கள்: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

#### `faq:avenuepark:pricing:ta`

- **Project:** avenuepark
- **Intent:** pricing
- **Category:** pricing
- **Language:** ta
- **Title:** விலை என்ன?
- **Metadata:** source=projects@2026.07.15:avenuepark:pricing, answer=Casagrand Avenuepark விலை: INR 65 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

**Text**

Q: விலை என்ன?
A: Casagrand Avenuepark விலை: INR 65 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

#### `faq:avenuepark:location:ta`

- **Project:** avenuepark
- **Intent:** location
- **Category:** location
- **Language:** ta
- **Title:** இடம் எங்கே?
- **Metadata:** source=projects@2026.07.15:avenuepark:location, answer=Casagrand Avenuepark இடம்: Tambaram / South Chennai corridor (demo) (Chennai).

**Text**

Q: இடம் எங்கே?
A: Casagrand Avenuepark இடம்: Tambaram / South Chennai corridor (demo) (Chennai).

#### `faq:avenuepark:amenities:ta`

- **Project:** avenuepark
- **Intent:** amenities
- **Category:** amenities
- **Language:** ta
- **Title:** வசதிகள் என்ன?
- **Metadata:** source=projects@2026.07.15:avenuepark:amenities, answer=Casagrand Avenuepark வசதிகள்: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance.

**Text**

Q: வசதிகள் என்ன?
A: Casagrand Avenuepark வசதிகள்: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance.

#### `faq:avenuepark:site_visit:ta`

- **Project:** avenuepark
- **Intent:** site_visit
- **Category:** site_visit
- **Language:** ta
- **Title:** தள வருகை புக் செய்யலாமா?
- **Metadata:** source=projects@2026.07.15:avenuepark:site_visit, answer=Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window. வசதியான நாள் சொல்லுங்கள்.

**Text**

Q: தள வருகை புக் செய்யலாமா?
A: Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window. வசதியான நாள் சொல்லுங்கள்.

#### `faq:avenuepark:callback:ta`

- **Project:** avenuepark
- **Intent:** callback
- **Category:** callback
- **Language:** ta
- **Title:** கால்பேக் ஏற்பாடு செய்யுங்கள்
- **Metadata:** source=projects@2026.07.15:avenuepark:callback, answer=Casagrand Avenuepark குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். விருப்பமான நேரம் சொல்லுங்கள்.

**Text**

Q: கால்பேக் ஏற்பாடு செய்யுங்கள்
A: Casagrand Avenuepark குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். விருப்பமான நேரம் சொல்லுங்கள்.

#### `faq:avenuepark:brochure:ta`

- **Project:** avenuepark
- **Intent:** brochure
- **Category:** brochure
- **Language:** ta
- **Title:** brochure அனுப்புங்கள்
- **Metadata:** source=projects@2026.07.15:avenuepark:brochure, answer=I can arrange the Avenuepark brochure through our advisor team. உங்கள் விருப்பத்தை பதிவு செய்தேன்.

**Text**

Q: brochure அனுப்புங்கள்
A: I can arrange the Avenuepark brochure through our advisor team. உங்கள் விருப்பத்தை பதிவு செய்தேன்.

#### `faq:avenuepark:greeting:ta`

- **Project:** avenuepark
- **Intent:** greeting
- **Category:** greeting
- **Language:** ta
- **Title:** hello / vanakkam
- **Metadata:** source=projects@2026.07.15:avenuepark:introduction, answer=வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று Casagrand Avenuepark பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. தொடர அனுமதி இருக்கிறதா?

**Text**

Q: hello / vanakkam
A: வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று Casagrand Avenuepark பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. தொடர அனுமதி இருக்கிறதா?

#### `faq:avenuepark:education:ta`

- **Project:** avenuepark
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** ta
- **Title:** brochure summary / project overview
- **Metadata:** source=projects@2026.07.15:avenuepark:education, answer=Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?

**Text**

Q: brochure summary / project overview
A: Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?

#### `faq:avenuepark:ood:ta`

- **Project:** avenuepark
- **Intent:** out_of_domain
- **Category:** fallback
- **Language:** ta
- **Title:** out of domain
- **Metadata:** source=projects@2026.07.15:avenuepark:safe_fallback, answer=நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

**Text**

Q: out of domain
A: நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

#### `faq:avenuepark:project_info:tanglish`

- **Project:** avenuepark
- **Intent:** project_info
- **Category:** project_info
- **Language:** tanglish
- **Title:** project pathi sollunga
- **Metadata:** source=projects@2026.07.15:avenuepark:project_info, answer=Casagrand Avenuepark — 2 & 3 BHK apartments @ Tambaram / South Chennai corridor (demo). Status: upcoming / booking open (demo). Highlights: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

**Text**

Q: project pathi sollunga
A: Casagrand Avenuepark — 2 & 3 BHK apartments @ Tambaram / South Chennai corridor (demo). Status: upcoming / booking open (demo). Highlights: Focused on value and practical layouts; Access to key southern transit nodes; Amenities planned for everyday family use.

#### `faq:avenuepark:pricing:tanglish`

- **Project:** avenuepark
- **Intent:** pricing
- **Category:** pricing
- **Language:** tanglish
- **Title:** pricing evlo?
- **Metadata:** source=projects@2026.07.15:avenuepark:pricing, answer=Casagrand Avenuepark pricing: INR 65 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

**Text**

Q: pricing evlo?
A: Casagrand Avenuepark pricing: INR 65 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

#### `faq:avenuepark:location:tanglish`

- **Project:** avenuepark
- **Intent:** location
- **Category:** location
- **Language:** tanglish
- **Title:** location enge?
- **Metadata:** source=projects@2026.07.15:avenuepark:location, answer=Casagrand Avenuepark location: Tambaram / South Chennai corridor (demo) (Chennai).

**Text**

Q: location enge?
A: Casagrand Avenuepark location: Tambaram / South Chennai corridor (demo) (Chennai).

#### `faq:avenuepark:amenities:tanglish`

- **Project:** avenuepark
- **Intent:** amenities
- **Category:** amenities
- **Language:** tanglish
- **Title:** amenities enna?
- **Metadata:** source=projects@2026.07.15:avenuepark:amenities, answer=Casagrand Avenuepark amenities: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance.

**Text**

Q: amenities enna?
A: Casagrand Avenuepark amenities: clubhouse, jogging track, indoor games, multipurpose hall, CCTV surveillance.

#### `faq:avenuepark:site_visit:tanglish`

- **Project:** avenuepark
- **Intent:** site_visit
- **Category:** site_visit
- **Language:** tanglish
- **Title:** site visit book pannalama?
- **Metadata:** source=projects@2026.07.15:avenuepark:site_visit, answer=Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window. Convenient day sollunga.

**Text**

Q: site visit book pannalama?
A: Avenuepark site visits can be scheduled. We will share access instructions and a preferred visit window. Convenient day sollunga.

#### `faq:avenuepark:callback:tanglish`

- **Project:** avenuepark
- **Intent:** callback
- **Category:** callback
- **Language:** tanglish
- **Title:** callback arrange pannunga
- **Metadata:** source=projects@2026.07.15:avenuepark:callback, answer=Casagrand Avenuepark pathi callback arrange panren. Preferred time sollunga.

**Text**

Q: callback arrange pannunga
A: Casagrand Avenuepark pathi callback arrange panren. Preferred time sollunga.

#### `faq:avenuepark:brochure:tanglish`

- **Project:** avenuepark
- **Intent:** brochure
- **Category:** brochure
- **Language:** tanglish
- **Title:** brochure anuppunga
- **Metadata:** source=projects@2026.07.15:avenuepark:brochure, answer=I can arrange the Avenuepark brochure through our advisor team. Request register paniren.

**Text**

Q: brochure anuppunga
A: I can arrange the Avenuepark brochure through our advisor team. Request register paniren.

#### `faq:avenuepark:greeting:tanglish`

- **Project:** avenuepark
- **Intent:** greeting
- **Category:** greeting
- **Language:** tanglish
- **Title:** hello / vanakkam
- **Metadata:** source=projects@2026.07.15:avenuepark:introduction, answer=Vanakkam! Naan Casagrand voice assistant. Indha call la Casagrand Avenuepark pathi discuss pannalam — amenities, location, pricing, site visit. Continue panna okay va?

**Text**

Q: hello / vanakkam
A: Vanakkam! Naan Casagrand voice assistant. Indha call la Casagrand Avenuepark pathi discuss pannalam — amenities, location, pricing, site visit. Continue panna okay va?

#### `faq:avenuepark:education:tanglish`

- **Project:** avenuepark
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** tanglish
- **Title:** brochure summary / project overview
- **Metadata:** source=projects@2026.07.15:avenuepark:education, answer=Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. Innum details venuma — amenities, pricing, illa location?

**Text**

Q: brochure summary / project overview
A: Casagrand Avenuepark is positioned for buyers seeking balanced pricing with essential lifestyle amenities in South Chennai. Layouts focus on usable space and community facilities. Innum details venuma — amenities, pricing, illa location?

#### `faq:avenuepark:ood:tanglish`

- **Project:** avenuepark
- **Intent:** out_of_domain
- **Category:** fallback
- **Language:** tanglish
- **Title:** out of domain
- **Metadata:** source=projects@2026.07.15:avenuepark:safe_fallback, answer=Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

**Text**

Q: out of domain
A: Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

#### `faq:mercury:project_info:en`

- **Project:** mercury
- **Intent:** project_info
- **Category:** project_info
- **Language:** en
- **Title:** Tell me about the project
- **Metadata:** source=projects@2026.07.15:mercury:project_info, answer=Casagrand Mercury offers premium 2 & 3 BHK apartments at OMR / IT corridor adjacency (demo). Status: launch / early booking (demo). Highlights: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

**Text**

Q: Tell me about the project
A: Casagrand Mercury offers premium 2 & 3 BHK apartments at OMR / IT corridor adjacency (demo). Status: launch / early booking (demo). Highlights: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

#### `faq:mercury:pricing:en`

- **Project:** mercury
- **Intent:** pricing
- **Category:** pricing
- **Language:** en
- **Title:** What is the pricing?
- **Metadata:** source=projects@2026.07.15:mercury:pricing, answer=Casagrand Mercury pricing starts at INR 90 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

**Text**

Q: What is the pricing?
A: Casagrand Mercury pricing starts at INR 90 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

#### `faq:mercury:location:en`

- **Project:** mercury
- **Intent:** location
- **Category:** location
- **Language:** en
- **Title:** Where is the project located?
- **Metadata:** source=projects@2026.07.15:mercury:location, answer=Casagrand Mercury is located at OMR / IT corridor adjacency (demo) (Chennai).

**Text**

Q: Where is the project located?
A: Casagrand Mercury is located at OMR / IT corridor adjacency (demo) (Chennai).

#### `faq:mercury:amenities:en`

- **Project:** mercury
- **Intent:** amenities
- **Category:** amenities
- **Language:** en
- **Title:** What amenities are available?
- **Metadata:** source=projects@2026.07.15:mercury:amenities, answer=Casagrand Mercury amenities include: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo).

**Text**

Q: What amenities are available?
A: Casagrand Mercury amenities include: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo).

#### `faq:mercury:site_visit:en`

- **Project:** mercury
- **Intent:** site_visit
- **Category:** site_visit
- **Language:** en
- **Title:** Can I book a site visit?
- **Metadata:** source=projects@2026.07.15:mercury:site_visit, answer=Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk. Which day works for you?

**Text**

Q: Can I book a site visit?
A: Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk. Which day works for you?

#### `faq:mercury:callback:en`

- **Project:** mercury
- **Intent:** callback
- **Category:** callback
- **Language:** en
- **Title:** Please arrange a callback
- **Metadata:** source=projects@2026.07.15:mercury:callback, answer=I'll arrange a callback about Casagrand Mercury. What time works best?

**Text**

Q: Please arrange a callback
A: I'll arrange a callback about Casagrand Mercury. What time works best?

#### `faq:mercury:brochure:en`

- **Project:** mercury
- **Intent:** brochure
- **Category:** brochure
- **Language:** en
- **Title:** Please send the brochure
- **Metadata:** source=projects@2026.07.15:mercury:brochure, answer=I can arrange the Mercury brochure for early registrants. I've noted your request.

**Text**

Q: Please send the brochure
A: I can arrange the Mercury brochure for early registrants. I've noted your request.

#### `faq:mercury:greeting:en`

- **Project:** mercury
- **Intent:** greeting
- **Category:** greeting
- **Language:** en
- **Title:** hello / vanakkam
- **Metadata:** source=projects@2026.07.15:mercury:introduction, answer=Hello! I'm the Casagrand voice assistant. Today we can talk about Casagrand Mercury — amenities, location, pricing, and booking a site visit. May I continue?

**Text**

Q: hello / vanakkam
A: Hello! I'm the Casagrand voice assistant. Today we can talk about Casagrand Mercury — amenities, location, pricing, and booking a site visit. May I continue?

#### `faq:mercury:education:en`

- **Project:** mercury
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** en
- **Title:** brochure summary / project overview
- **Metadata:** source=projects@2026.07.15:mercury:education, answer=Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. Would you like amenities, pricing, or location next?

**Text**

Q: brochure summary / project overview
A: Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. Would you like amenities, pricing, or location next?

#### `faq:mercury:ood:en`

- **Project:** mercury
- **Intent:** out_of_domain
- **Category:** fallback
- **Language:** en
- **Title:** out of domain
- **Metadata:** source=projects@2026.07.15:mercury:safe_fallback, answer=I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

**Text**

Q: out of domain
A: I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

#### `faq:mercury:project_info:ta`

- **Project:** mercury
- **Intent:** project_info
- **Category:** project_info
- **Language:** ta
- **Title:** திட்டம் பற்றி சொல்லுங்கள்
- **Metadata:** source=projects@2026.07.15:mercury:project_info, answer=Casagrand Mercury — premium 2 & 3 BHK apartments @ OMR / IT corridor adjacency (demo). நிலை: launch / early booking (demo). முக்கிய அம்சங்கள்: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

**Text**

Q: திட்டம் பற்றி சொல்லுங்கள்
A: Casagrand Mercury — premium 2 & 3 BHK apartments @ OMR / IT corridor adjacency (demo). நிலை: launch / early booking (demo). முக்கிய அம்சங்கள்: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

#### `faq:mercury:pricing:ta`

- **Project:** mercury
- **Intent:** pricing
- **Category:** pricing
- **Language:** ta
- **Title:** விலை என்ன?
- **Metadata:** source=projects@2026.07.15:mercury:pricing, answer=Casagrand Mercury விலை: INR 90 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

**Text**

Q: விலை என்ன?
A: Casagrand Mercury விலை: INR 90 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

#### `faq:mercury:location:ta`

- **Project:** mercury
- **Intent:** location
- **Category:** location
- **Language:** ta
- **Title:** இடம் எங்கே?
- **Metadata:** source=projects@2026.07.15:mercury:location, answer=Casagrand Mercury இடம்: OMR / IT corridor adjacency (demo) (Chennai).

**Text**

Q: இடம் எங்கே?
A: Casagrand Mercury இடம்: OMR / IT corridor adjacency (demo) (Chennai).

#### `faq:mercury:amenities:ta`

- **Project:** mercury
- **Intent:** amenities
- **Category:** amenities
- **Language:** ta
- **Title:** வசதிகள் என்ன?
- **Metadata:** source=projects@2026.07.15:mercury:amenities, answer=Casagrand Mercury வசதிகள்: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo).

**Text**

Q: வசதிகள் என்ன?
A: Casagrand Mercury வசதிகள்: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo).

#### `faq:mercury:site_visit:ta`

- **Project:** mercury
- **Intent:** site_visit
- **Category:** site_visit
- **Language:** ta
- **Title:** தள வருகை புக் செய்யலாமா?
- **Metadata:** source=projects@2026.07.15:mercury:site_visit, answer=Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk. வசதியான நாள் சொல்லுங்கள்.

**Text**

Q: தள வருகை புக் செய்யலாமா?
A: Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk. வசதியான நாள் சொல்லுங்கள்.

#### `faq:mercury:callback:ta`

- **Project:** mercury
- **Intent:** callback
- **Category:** callback
- **Language:** ta
- **Title:** கால்பேக் ஏற்பாடு செய்யுங்கள்
- **Metadata:** source=projects@2026.07.15:mercury:callback, answer=Casagrand Mercury குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். விருப்பமான நேரம் சொல்லுங்கள்.

**Text**

Q: கால்பேக் ஏற்பாடு செய்யுங்கள்
A: Casagrand Mercury குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். விருப்பமான நேரம் சொல்லுங்கள்.

#### `faq:mercury:brochure:ta`

- **Project:** mercury
- **Intent:** brochure
- **Category:** brochure
- **Language:** ta
- **Title:** brochure அனுப்புங்கள்
- **Metadata:** source=projects@2026.07.15:mercury:brochure, answer=I can arrange the Mercury brochure for early registrants. உங்கள் விருப்பத்தை பதிவு செய்தேன்.

**Text**

Q: brochure அனுப்புங்கள்
A: I can arrange the Mercury brochure for early registrants. உங்கள் விருப்பத்தை பதிவு செய்தேன்.

#### `faq:mercury:greeting:ta`

- **Project:** mercury
- **Intent:** greeting
- **Category:** greeting
- **Language:** ta
- **Title:** hello / vanakkam
- **Metadata:** source=projects@2026.07.15:mercury:introduction, answer=வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று Casagrand Mercury பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. தொடர அனுமதி இருக்கிறதா?

**Text**

Q: hello / vanakkam
A: வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று Casagrand Mercury பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. தொடர அனுமதி இருக்கிறதா?

#### `faq:mercury:education:ta`

- **Project:** mercury
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** ta
- **Title:** brochure summary / project overview
- **Metadata:** source=projects@2026.07.15:mercury:education, answer=Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?

**Text**

Q: brochure summary / project overview
A: Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?

#### `faq:mercury:ood:ta`

- **Project:** mercury
- **Intent:** out_of_domain
- **Category:** fallback
- **Language:** ta
- **Title:** out of domain
- **Metadata:** source=projects@2026.07.15:mercury:safe_fallback, answer=நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

**Text**

Q: out of domain
A: நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

#### `faq:mercury:project_info:tanglish`

- **Project:** mercury
- **Intent:** project_info
- **Category:** project_info
- **Language:** tanglish
- **Title:** project pathi sollunga
- **Metadata:** source=projects@2026.07.15:mercury:project_info, answer=Casagrand Mercury — premium 2 & 3 BHK apartments @ OMR / IT corridor adjacency (demo). Status: launch / early booking (demo). Highlights: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

**Text**

Q: project pathi sollunga
A: Casagrand Mercury — premium 2 & 3 BHK apartments @ OMR / IT corridor adjacency (demo). Status: launch / early booking (demo). Highlights: Designed for professionals along the IT corridor; Premium finishes and elevated amenities (demo framing); Priority site visits for early registrants.

#### `faq:mercury:pricing:tanglish`

- **Project:** mercury
- **Intent:** pricing
- **Category:** pricing
- **Language:** tanglish
- **Title:** pricing evlo?
- **Metadata:** source=projects@2026.07.15:mercury:pricing, answer=Casagrand Mercury pricing: INR 90 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

**Text**

Q: pricing evlo?
A: Casagrand Mercury pricing: INR 90 Lakh onwards (indicative demo). Indicative demo pricing only; final quote after site discussion.

#### `faq:mercury:location:tanglish`

- **Project:** mercury
- **Intent:** location
- **Category:** location
- **Language:** tanglish
- **Title:** location enge?
- **Metadata:** source=projects@2026.07.15:mercury:location, answer=Casagrand Mercury location: OMR / IT corridor adjacency (demo) (Chennai).

**Text**

Q: location enge?
A: Casagrand Mercury location: OMR / IT corridor adjacency (demo) (Chennai).

#### `faq:mercury:amenities:tanglish`

- **Project:** mercury
- **Intent:** amenities
- **Category:** amenities
- **Language:** tanglish
- **Title:** amenities enna?
- **Metadata:** source=projects@2026.07.15:mercury:amenities, answer=Casagrand Mercury amenities: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo).

**Text**

Q: amenities enna?
A: Casagrand Mercury amenities: premium clubhouse, infinity / leisure pool, work-from-home lounge, sky deck, concierge desk (demo).

#### `faq:mercury:site_visit:tanglish`

- **Project:** mercury
- **Intent:** site_visit
- **Category:** site_visit
- **Language:** tanglish
- **Title:** site visit book pannalama?
- **Metadata:** source=projects@2026.07.15:mercury:site_visit, answer=Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk. Convenient day sollunga.

**Text**

Q: site visit book pannalama?
A: Mercury early tour slots are limited. We can reserve a visit and share a callback from the sales desk. Convenient day sollunga.

#### `faq:mercury:callback:tanglish`

- **Project:** mercury
- **Intent:** callback
- **Category:** callback
- **Language:** tanglish
- **Title:** callback arrange pannunga
- **Metadata:** source=projects@2026.07.15:mercury:callback, answer=Casagrand Mercury pathi callback arrange panren. Preferred time sollunga.

**Text**

Q: callback arrange pannunga
A: Casagrand Mercury pathi callback arrange panren. Preferred time sollunga.

#### `faq:mercury:brochure:tanglish`

- **Project:** mercury
- **Intent:** brochure
- **Category:** brochure
- **Language:** tanglish
- **Title:** brochure anuppunga
- **Metadata:** source=projects@2026.07.15:mercury:brochure, answer=I can arrange the Mercury brochure for early registrants. Request register paniren.

**Text**

Q: brochure anuppunga
A: I can arrange the Mercury brochure for early registrants. Request register paniren.

#### `faq:mercury:greeting:tanglish`

- **Project:** mercury
- **Intent:** greeting
- **Category:** greeting
- **Language:** tanglish
- **Title:** hello / vanakkam
- **Metadata:** source=projects@2026.07.15:mercury:introduction, answer=Vanakkam! Naan Casagrand voice assistant. Indha call la Casagrand Mercury pathi discuss pannalam — amenities, location, pricing, site visit. Continue panna okay va?

**Text**

Q: hello / vanakkam
A: Vanakkam! Naan Casagrand voice assistant. Indha call la Casagrand Mercury pathi discuss pannalam — amenities, location, pricing, site visit. Continue panna okay va?

#### `faq:mercury:education:tanglish`

- **Project:** mercury
- **Intent:** brochure_summary
- **Category:** brochure
- **Language:** tanglish
- **Title:** brochure summary / project overview
- **Metadata:** source=projects@2026.07.15:mercury:education, answer=Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. Innum details venuma — amenities, pricing, illa location?

**Text**

Q: brochure summary / project overview
A: Casagrand Mercury targets buyers who want a premium apartment experience with work-friendly amenities near the OMR corridor. It emphasizes elevated club facilities and contemporary living. Innum details venuma — amenities, pricing, illa location?

#### `faq:mercury:ood:tanglish`

- **Project:** mercury
- **Intent:** out_of_domain
- **Category:** fallback
- **Language:** tanglish
- **Title:** out of domain
- **Metadata:** source=projects@2026.07.15:mercury:safe_fallback, answer=Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

**Text**

Q: out of domain
A: Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.

### Record type: `escalation` (6)

#### `escalation:handoff:en`

- **Project:** —
- **Intent:** human_handoff
- **Category:** escalation
- **Language:** en
- **Title:** human_handoff
- **Metadata:** action=handoff, reason=caller_requested_human

**Text**

Sure — I'll arrange a human handoff. A Casagrand advisor will continue from here. Please stay on the line.

#### `escalation:ood_escalation:en`

- **Project:** —
- **Intent:** out_of_domain
- **Category:** escalation
- **Language:** en
- **Title:** out_of_domain
- **Metadata:** action=safe_fallback, reason=out_of_domain_topic

**Text**

I can help with Casagrand project details, pricing ranges, location, amenities, site visits, callbacks, and brochures. For anything else, I can connect you to a human advisor.

#### `escalation:handoff:ta`

- **Project:** —
- **Intent:** human_handoff
- **Category:** escalation
- **Language:** ta
- **Title:** human_handoff
- **Metadata:** action=handoff, reason=caller_requested_human

**Text**

சரி — மனித ஆலோசகருக்கு இணைக்கிறேன். Casagrand ஆலோசகர் தொடர்ந்து உதவுவார். தயவுசெய்து காத்திருக்கவும்.

#### `escalation:ood_escalation:ta`

- **Project:** —
- **Intent:** out_of_domain
- **Category:** escalation
- **Language:** ta
- **Title:** out_of_domain
- **Metadata:** action=safe_fallback, reason=out_of_domain_topic

**Text**

நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்.

#### `escalation:handoff:tanglish`

- **Project:** —
- **Intent:** human_handoff
- **Category:** escalation
- **Language:** tanglish
- **Title:** human_handoff
- **Metadata:** action=handoff, reason=caller_requested_human

**Text**

Sure — human advisor ku connect panren. Casagrand advisor continue pannuvaanga. Please wait pannunga.

#### `escalation:ood_escalation:tanglish`

- **Project:** —
- **Intent:** out_of_domain
- **Category:** escalation
- **Language:** tanglish
- **Title:** out_of_domain
- **Metadata:** action=safe_fallback, reason=out_of_domain_topic

**Text**

Naan Casagrand project details, pricing, location, amenities, site visit, callback, brochure la help panna mudiyum. Vera topic na human advisor connect panni tharen.


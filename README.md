**Planet Mould is a programme of research, design and public engagement that explores how we will live with Filamentous microfungi - or moulds - in a climate changed world.**

This open source Github Repository hosts critical digital resources developed to support life on Planet Mould.   

**MOULDWIRE**

Mouldwire is a bespoke science and media news service designed to collect and distribute the latest mould related research, news and stories. This version is optimised for social scientists interested in planetary health, infrastructure, and human/non-human sociality. 

The search engine is based on RSS feeds for ~50 international peer reviewed scientific journals; public health agencies, environmental bodies, and standards organisations, news organisations; and social media platforms. These are scanned for updates 4 times/day using a unique list of keywords. Each item is accompanied by a brief summary that has been prompt engineered using Meta-Llama-3-8B-Instruct to explore the connections between these reports to broader anthropological qustions. 

Mouldwire launched in Jan 2026 and is currently under active development. 

A full list of RSS Feeds and keywords used in Mouldwire can be found below.




**KEYWORDS**

SUBJECTS = ['mould', 'mold', 'mycotoxin', 'aflatoxin', 'aspergillus', 'penicillium', 'stachybotrys', 'cladosporium', 'alternaria', 'fusarium', 'mucor', 'filamentous']

CONTEXTS = ['resistance', 'amr', 'famr', 'infection', 'clinical', 'indoor air', 'housing', 'home', 'building', 'hvac', 'ventilation', 'azole', 'pathogen', 'humidity', 'condensation', 'iaq', 'antifungal', 'mask', 'surgical', 'degradation', 'environmental', 'fabric', 'damp', 'bioaerosol', 'environment', 'bioremediation', 'exposure', 'public health', 'study', 'analysis', 'climate', 'heat', 'metabolic', 'metabolise', 'metabolize', 'infrastructure', 'materiality', 'biopolitics', 'labor', 'urban', 'decay', 'toxicity', 'assemblage', 'sociality', 'precarity', 'policy', 'regulation', 'governance', 'justice', 'inequality', 'tenure']

**SOURCES**

Mouldwire uses RSS feeds from a mixed ecology of sources: including primary research journals (MDPI, Frontiers, ASM, ACS, Elsevier); high-impact general science journals (Nature, PLOS), public health organisations and science journalism.

RSS_FEEDS = 
    "science":
        "https://www.nature.com/srep.rss",
        "https://www.nature.com/ncomms.rss",
        "https://www.nature.com/natrevearthenviron.rss",
        "https://www.cell.com/current-biology/current.rss",
        "https://journals.plos.org/plosone/feed/atom",
        "https://www.mdpi.com/rss/journal/jof",
        "https://www.mdpi.com/rss/journal/microorganisms",
        "https://www.mdpi.com/rss/journal/molecules",
        "https://onlinelibrary.wiley.com/action/showFeed?jc=10970010&type=etoc&feed=rss",
        "https://www.mdpi.com/rss/journal/biomolecules",
        "https://www.mdpi.com/rss/journal/ijms",
        "https://journals.asm.org/action/showFeed?feed=rss&jc=MBIO&type=etoc",
        "https://journals.asm.org/action/showFeed?feed=rss&jc=SPECTRUM&type=etoc",
        "https://www.frontiersin.org/journals/microbiology/rss",
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=acsodf",
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jacsat",
        "https://rss.sciencedirect.com/publication/science/01418130",
        "https://www.tandfonline.com/feed/rss/tmyc20", # Mycology
        "https://rss.sciencedirect.com/publication/science/18786146", # Fungal Biology
        "https://rss.sciencedirect.com/publication/science/17494613", # Fungal Biology Reviews
        "https://www.tandfonline.com/feed/rss/umyc20", # Mycologia
        "https://onlinelibrary.wiley.com/feed/14683083/most-recent", # Environmental Microbiology
        "https://www.studiesinmycology.org/index.php/sim/gateway/plugin/WebFeedGatewayPlugin/rss2",
        "https://www.ingentaconnect.com/content/asb/pers/latest?format=rss", # Persoonia
        "https://www.microbiologyresearch.org/rss/content/journal/micro/latestarticles?fmt=rss",
        "https://rss.sciencedirect.com/publication/science/10871845", # Fungal Genetics and Biology
        "https://www.nature.com/nmicrobiol.rss" # Nature Microbiology
        "https://www.microbiologyresearch.org/rss/content/journal/jmm/latest?fmt=rss", 
        "https://academic.oup.com/rss/site_6222/4034.xml", # Journal of Fungi
        "https://www.ncbi.nlm.nih.gov/feed/rss.cgi?ChanKey=PubMedNews",
        "https://link.springer.com/search.rss?facet-content-type=Article&facet-journal-        id=15010&sortOrder=newestFirst",


    "media":
        "https://www.sciencedaily.com/rss/plants_animals/fungi.xml",
        "https://phys.org/rss-feed/biology-news/microbiology/",
        "https://theconversation.com/articles.atom",
        "https://allafrica.com/rss/main/main.xml",
        "https://news.mongabay.com/feed/",
        "https://rss.buzzsprout.com/1257893.rss",
        "https://www.scidev.net/asia-pacific/rss.xml",
        "https://www.scidev.net/sub-saharan-africa/rss.xml",


    "health":
        "https://www.mdpi.com/rss/journal/toxins",
        "https://www.thelancet.com/laninf.xml",
        "https://www.sciencedirect.com/journal/acta-tropica/rss",
        "https://www.cdc.gov/media/rss/topic/fungal.xml",
        "https://www.mdpi.com/rss/journal/animals",
        "https://www.mdpi.com/rss/journal/plants",
        "https://www.mdpi.com/rss/journal/agronomy",
        "https://www.frontiersin.org/journals/plant-science/rss",
        "https://www.frontiersin.org/journals/veterinary-science/rss",
        "https://www.mdpi.com/rss/journal/foods",
        "https://rss.sciencedirect.com/publication/science/03088146",
        "https://rss.sciencedirect.com/publication/science/09639969",
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jafcau",
        "https://www.mdpi.com/rss/journal/marinedrugs",
        "https://www.mdpi.com/rss/journal/antibiotics",
        "https://www.wageningenacademic.com/action/showFeed?jc=wmj&type=etoc&feed=rss", # World Mycotoxin Journal
        "https://www.tandfonline.com/feed/rss/tfac20", # Food Additives & Contaminants
        "https://link.springer.com/search.rss?facet-content-type=Article&facet-journal-id=12550", # Mycotoxin Research
        "https://meridian.allenpress.com/jfp/rss", # Journal of Food Protection
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=afsthl", # ACS Food Science & Tech
        "https://rss.sciencedirect.com/publication/science/09567135", # Food Control
        "https://rss.sciencedirect.com/publication/science/07400020", # Food Microbiology
        "https://rss.sciencedirect.com/publication/science/22147993", # Current Opinion in Food Science
        "https://www.sciencedirect.com/journal/one-health/rss", # One Health
        "https://www.govwire.co.uk/rss/department-of-health-and-social-care.atom", # UK DHSC
        "https://www.govwire.co.uk/rss/foreign-commonwealth-development-office", 
        "https://www.govwire.co.uk/rss/department-for-environment-food-rural-affairs",
        "https://www.govwire.co.uk/rss/department-for-science-innovation-and-technology",
        
    "indoor":
        "https://journals.asm.org/action/showFeed?feed=rss&jc=AEM&type=etoc",
        "https://www.ashrae.org/RssFeeds/news-feed.xml",
        "https://www.gov.uk/search/news-and-communications.atom?content_store_document_type=news_story&organisations[]=department-for-levelling-up-housing-and-communities",
        "https://www.mdpi.com/rss/journal/fermentation",
        "https://www.mdpi.com/rss/journal/catalysts",
        "https://www.mdpi.com/rss/journal/applsci",
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jnprdf",
        "https://rss.sciencedirect.com/publication/science/09608524",
        "https://rss.sciencedirect.com/publication/science/00489697",
        "https://rss.sciencedirect.com/publication/science/02697491",
        "https://rss.sciencedirect.com/publication/science/03043894",
        "https://rss.sciencedirect.com/publication/science/13858947",
        "https://rss.sciencedirect.com/publication/science/09619534",
        "https://onlinelibrary.wiley.com/action/showFeed?jc=16000668&type=etoc&feed=rss", # Indoor Air
        "https://rss.sciencedirect.com/publication/science/03601323", # Building and Environment
        "https://healthyindoors.com/feed/", # Healthy Indoor Magazine
        "https://www.nature.com/jes.rss", # Journal of Exposure Science
        "https://ehp.niehs.nih.gov/action/showFeed?type=etoc&feed=rss&jc=ehp", # Env Health Perspectives
        "https://rss.sciencedirect.com/publication/science/13522310", # Atmospheric Environment
        "https://verifyairqualitytest.ca/feed/", # Verify Air Quality Blog
        "https://smartairfilters.com/en/feed/", # Smart Air Blog
        "https://rss.sciencedirect.com/publication/science/23527102", # Journal of Building Engineering
        "https://www.gov.uk/government/organisations/uk-health-security-agency.atom", # UKHSA
        "https://www.sciencedirect.com/journal/journal-of-building-engineering/rss",
        "https://www.frontiersin.org/journals/public-health/rss",   
        "https://abc2.net/index.php/journal/gateway/plugin/WebFeedGatewayPlugin/rss2",  
        "https://advanced.onlinelibrary.wiley.com/feed/15214095/most-recent",   
        "https://www.sciencedirect.com/journal/building-and-environment/rss",

    
    "clinical":
        "https://journals.plos.org/plospathogens/feed/atom",
        "https://www.benthamdirect.com/content/journals/cpb/fasttrack?feed=rss",
        "https://verjournal.com/index.php/ver/gateway/plugin/WebFeedGatewayPlugin/rss2",
        "https://www.mdpi.com/rss/journal/antibiotics",
        "https://www.mdpi.com/rss/journal/pathogens",
        "https://www.mdpi.com/rss/journal/pharmaceuticals",
        "https://www.mdpi.com/rss/journal/diagnostics",
        "https://journals.asm.org/action/showFeed?feed=rss&jc=AAC&type=etoc",
        "https://journals.asm.org/action/showFeed?feed=rss&jc=JCM&type=etoc",
        "https://www.frontiersin.org/journals/cellular-and-infection-microbiology/rss",
        "https://www.frontiersin.org/journals/medicine/rss",
        "https://www.frontiersin.org/journals/immunology/rss",
        "https://www.frontiersin.org/journals/pharmacology/rss",
        "https://academic.oup.com/rss/site_5376/3452.xml", # Medical Mycology
        "https://academic.oup.com/rss/site_5204/3169.xml", # Journal of Antimicrobial Chemotherapy
        "https://journals.asm.org/action/showFeed?feed=rss&jc=cmr&type=etoc", # Clinical Microbiology Reviews
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=aidcbc", # ACS Infectious Diseases
        "https://www.thelancet.com/rssfeed/laninf_current.xml", # Lancet Infectious Diseases
        "https://rss.sciencedirect.com/publication/science/07328893", # Diagnostic Microbiology
        "https://rss.sciencedirect.com/publication/science/01634453", # Journal of Infection
        "https://onlinelibrary.wiley.com/action/showFeed?jc=14390507&type=etoc&feed=rss" # Mycoses


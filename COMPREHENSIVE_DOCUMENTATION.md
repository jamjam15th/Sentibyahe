# Comprehensive Documentation Report
## Land Public Transportation · Sentiment Analysis Platform

---

## High-Level Overview

This is a **Streamlit-based survey and sentiment analysis platform** designed specifically for collecting and analyzing customer feedback on land public transportation services. The platform enables transportation agencies to create custom feedback surveys, collect responses from passengers via a public form, automatically analyze sentiment from text responses, and visualize insights through a comprehensive dashboard. It solves the critical problem of transforming unstructured passenger feedback into structured, actionable intelligence using machine learning sentiment analysis and the SERVQUAL framework to measure service quality across five key dimensions.

---

## Sitemap & Page Breakdown

### 1. **Login & Authentication** (`login.py`)
   - **Purpose**: Secure user authentication and registration
   - **Main Elements**:
     - Two-tab interface: "Sign In" and "Create Account"
     - Email and password input fields with validation
     - Split-screen design with branding on left (navy background) and form on right
     - Session management with device fingerprinting (User-Agent hashing)
     - Active session tracking in database
   - **Key Features**:
     - Supabase authentication integration
     - Device ID generation for multi-device sessions
     - User metadata storage (first_name, last_name)
     - Full-screen centered layout with custom CSS
     - Mobile-responsive design with hidden left panel on small screens
   - **User Flow**: User enters email/password → system validates against Supabase auth → creates session record → redirects to router/main app

---

### 2. **Router/Navigation Hub** (`router.py`)
   - **Purpose**: Central navigation and page routing for the application
   - **Main Elements**:
     - Sidebar navigation with collapsible menu
     - Custom styling with navy background and gold accents
     - Sidebar displays user profile section with email and name
     - Page links organized hierarchically
     - Hidden Streamlit native components (menu, footer, toolbar)
   - **Key Features**:
     - Dynamic sidebar rendering based on user session state
     - Navigation labels and sections (e.g., "Admin", "Forms", "Analysis")
     - Session state validation on each page load
   - **User Flow**: After login, users land on router → select desired page from sidebar → router navigates to appropriate page

---

### 3. **Form Builder** (`builder.py`)
   - **Purpose**: Create and configure custom feedback surveys
   - **Main Elements**:
     - Form list sidebar showing all user forms (active and archived)
     - Form editor with drag-and-drop question management
     - Question type selector (Multiple Choice, Multiple Select, Likert Scale, Text Input, Text Area, Rating)
     - SERVQUAL dimension assignment for each question
     - Demographic settings toggle
     - Preview mode to see form as respondents will see it
     - Public link generation and sharing UI
   - **Key Features**:
     - Multi-form support (users can create unlimited forms)
     - Form-level metadata: title, description, demographic options
     - Question-level control: enable/disable sentiment analysis per question
     - Filter questions by SERVQUAL dimension or question type
     - Archive/restore forms without permanent deletion
     - Shareable public link with form ID embedded
     - Form versioning through updated_at timestamp
   - **User Flow**: 
     1. User clicks "New Form"
     2. Form created with unique ID
     3. User adds questions, assigns dimensions
     4. User configures sentiment analysis per question
     5. User previews form
     6. User shares public link via URL or copy-to-clipboard

---

### 4. **Public Survey Form** (`public_form.py`)
   - **Purpose**: Passenger-facing form for collecting feedback
   - **Main Elements**:
     - Centered, mobile-optimized form container
     - Form header with title and description
     - Dynamically rendered questions based on builder configuration
     - Question rendering varies by type:
       - Multiple Choice: vertical radio buttons
       - Multiple Select: vertical checkboxes
       - Likert Scale: horizontal 5-point buttons (squares)
       - Text Input: single-line text field
       - Text Area: multi-line text field
       - Rating: 1-5 star selection
     - Optional demographic section (if enabled by admin)
     - Submit button at bottom
     - Success/error messaging
   - **Key Features**:
     - Form accessed via query parameter: `?form_id={public_id}`
     - Allows multiple responses (controlled by form settings)
     - Captures client_submission_id for tracking
     - Responsive design for mobile passengers
     - Text responses stored for sentiment analysis
   - **User Flow**: Passenger clicks public link → sees form → completes survey → submits → data stored in database → sentiment analysis triggered automatically

---

### 5. **Dashboard** (`dashboard.py`)
   - **Purpose**: Real-time visualization of survey responses and sentiment insights
   - **Main Elements**:
     - Premium header with live badge (animated pulsing dot)
     - KPI cards showing:
       - Total responses count
       - Response rate percentage
       - Average overall rating
       - Pending analysis count
     - Demographic breakdown section with donut charts (if demographics enabled)
     - SERVQUAL dimension cards (5 cards: Tangibles, Reliability, Responsiveness, Assurance, Empathy)
     - Sentiment distribution bar charts
     - General ratings card
     - Response time-series chart
     - Detailed response table with filters/search
     - Tab-based navigation for different views
   - **Key Features**:
     - Form selector dropdown to switch between user's forms
     - Real-time data with auto-refresh
     - Sentiment visualization with color coding:
       - Positive (green): #4a7c59
       - Negative (red): #b03a2e
       - Neutral (muted blue): #8b9dc3
     - Time-range filtering (last 7/30 days, custom ranges)
     - Demographic filtering when applicable
     - Scale normalization (converts different Likert scales to 0-5 for comparison)
   - **User Flow**: User navigates to dashboard → selects form → dashboard loads real-time sentiment data → user views KPIs, charts, and response details

---

### 6. **Sentiment Analysis** (`sentiment_analysis.py`)
   - **Purpose**: Text-based sentiment classification and model comparison
   - **Main Elements**:
     - Premium header with description
     - Text input area for single-sentence analysis (playground)
     - Batch upload section for CSV file import
     - Model comparison interface allowing side-by-side analysis
     - Three result cards showing sentiment classification
     - Distribution percentage bar charts
     - Model selector dropdown with multiple baseline options
   - **Key Features**:
     - **Playground**: Paste or type text → system returns sentiment (Positive/Neutral/Negative) with confidence score
     - **Batch Upload**: Upload CSV with text column → system processes all rows → exports results
     - **Model Comparison**: Compare results between:
       - Our model: Fine-tuned XLM-RoBERTa (cardiffnlp/twitter-xlm-roberta-base-sentiment)
       - Twitter RoBERTa (cardiffnlp/twitter-roberta-base-sentiment-latest)
       - Multilingual BERT (nlptown/bert-base-multilingual-uncased-sentiment)
       - DistilBERT SST-2 (distilbert-base-uncased-finetuned-sst-2-english)
     - Automatic label normalization across different model output formats
     - Confidence score calculation and display
   - **User Flow**: User navigates to Analysis → chooses Playground or Batch Upload → enters/uploads text → system runs sentiment analysis → displays results → (optional) compares with baseline models

---

### 7. **Settings** (`settings.py`)
   - **Purpose**: User account and platform configuration
   - **Main Elements**:
     - User profile section (email, name)
     - Account security controls
     - Form management section
     - API key display (if applicable)
     - Export data options
     - Session management
     - Logout button
   - **Key Features**:
     - Premium header styling
     - Account information display
     - Session history (view active sessions)
     - Danger zone section for account deletion
   - **User Flow**: User clicks settings icon → navigates to settings page → updates preferences or logs out

---

## Core Features

### 1. **Authentication & Session Management**
   - **How it works**: 
     - Supabase handles user registration and password verification
     - On successful login, a session record is created with unique session_id and device_id
     - Session state stored in Streamlit's `st.session_state` and in database `active_sessions` table
     - Device fingerprint generated from User-Agent header to detect multi-device usage
     - Session persists across page navigations via session state
   - **Backend**: Supabase Authentication, custom session tracking table
   - **Data flow**: User credentials → Supabase auth.sign_in_with_password() → session created → user_email, first_name, last_name extracted to session state

---

### 2. **Multi-Form Management System**
   - **How it works**:
     - Each user can create unlimited surveys/forms
     - Each form has unique form_id (12-char UUID)
     - Forms stored in `form_list` table (tracks title, description, created_at, is_archived)
     - Forms have metadata in `form_meta` table (demographics settings, allow_multiple_responses flag, contact info)
     - Current form tracked in session state for quick access
     - Archived forms hidden by default but recoverable
   - **Backend**: Supabase tables: form_list, form_meta
   - **Data flow**: User creates form → form_id generated → entries added to both tables → form_id used as public identifier

---

### 3. **Question Builder & Form Configuration**
   - **How it works**:
     - Questions stored in `form_questions` table with:
       - question_id, form_id, question_text, question_type, order_index
       - dimension (SERVQUAL category)
       - enable_sentiment (boolean to control sentiment analysis per question)
       - is_required flag
       - options array (for multiple choice, rating, etc.)
     - Supports 6 question types:
       1. **Multiple Choice**: Single selection from options
       2. **Multiple Select**: Multiple selections from options
       3. **Likert Scale**: 5-point scale (radio buttons)
       4. **Text Input**: Single-line text response
       5. **Text Area**: Multi-line text response
       6. **Rating**: 1-5 star rating
     - SERVQUAL dimensions filter questions:
       - Tangibles (🚌): Vehicle/facility appearance
       - Reliability (🕐): Schedule adherence, predictability
       - Responsiveness (⚡): Speed of service
       - Assurance (🛡️): Safety and competence
       - Empathy (🤝): Understanding passenger needs
   - **Backend**: Supabase table: form_questions
   - **Data flow**: Builder UI → question definition → saved to form_questions → rendered in public form

---

### 4. **Sentiment Analysis Engine**
   - **How it works**:
     - Uses Hugging Face Transformers library with PyTorch
     - Primary model: **Fine-tuned XLM-RoBERTa** (cardiffnlp/twitter-xlm-roberta-base-sentiment)
       - Pre-trained on multilingual Twitter data
       - 3-class classifier: POSITIVE, NEUTRAL, NEGATIVE
       - Supports non-English text
     - Pipeline processes text input → tokenizes → runs through transformer → outputs label + confidence score
     - Automatically triggered on form submission for responses with `enable_sentiment=true`
     - Per-question sentiment stored in `form_responses.question_sentiments` JSON object
     - Structure: 
       ```json
       {
         "q1_id": {"text": "Great service", "enable_sentiment": true, "sentiment": "POSITIVE"},
         "q2_id": {"text": "Maria Lopez", "enable_sentiment": false, "sentiment": null}
       }
       ```
     - Batch processing available via CSV upload in Analysis page
     - Model comparison allows testing against 3 baselines with automatic label normalization
   - **Backend**: Transformers library, Torch CPU (specified in requirements.txt)
   - **Data flow**: Response submitted → questions with enable_sentiment=true identified → text extracted → sentiment pipeline processes → results stored → dashboard aggregates

---

### 5. **Response Collection & Storage**
   - **How it works**:
     - Public form submits responses to `form_responses` table
     - Each response record includes:
       - form_id, admin_email, response_id (UUID)
       - client_submission_id (for tracking unique respondents)
       - responses_json (all question answers stored as JSON)
       - question_sentiments (per-question sentiment analysis results)
       - demographics_json (if demographics enabled)
       - overall_rating (derived from general rating question)
       - submitted_at timestamp
       - allows_multiple_responses flag (if form permits retakes)
     - Responses queryable by form_id, date range, sentiment, demographic filters
     - Client submission tracking prevents duplicate submissions (conditional)
   - **Backend**: Supabase table: form_responses with indexes on form_id, client_submission_id, question_sentiments
   - **Data flow**: Public form submit → responses_json validated → inserted into form_responses → triggers sentiment analysis background process → dashboard queries results for visualization

---

### 6. **Dashboard Analytics & Visualization**
   - **How it works**:
     - Real-time data aggregation from form_responses table
     - KPI calculations:
       - **Total responses**: COUNT of form_responses where form_id = current_form
       - **Response rate**: (responses / estimated_outreach) × 100
       - **Average rating**: AVG(overall_rating) normalized to 5-point scale
       - **Pending analysis**: COUNT where question_sentiments is null but enable_sentiment=true
     - **Dimension sentiment charts**: For each SERVQUAL dimension
       - Filters responses to questions tagged with that dimension
       - Aggregates sentiments: POSITIVE count, NEUTRAL count, NEGATIVE count
       - Calculates percentages for distribution bars
     - **Demographic breakdown**: If demographics enabled
       - Donut charts per demographic field (e.g., age group, passenger type)
       - Uses fixed multiple-choice options for donut generation
     - **Time-series chart**: Response submission trend over time
     - Scale normalization: Converts different Likert scales (3-point, 5-point, 10-point) to standardized 0-5 scale for comparison
     - Real-time refresh with polling (auto-rerun on form dropdown change)
   - **Backend**: Supabase queries with aggregations, Pandas for data manipulation, Altair/Plotly for visualization
   - **Data flow**: User selects form → dashboard queries form_responses → aggregates by sentiment/dimension → normalizes scales → renders charts

---

### 7. **Demographic Analysis (Optional)**
   - **How it works**:
     - Admins can enable demographics collection per form via `form_meta.include_demographics`
     - Demographic fields configured in builder (must be Multiple Choice or Multiple Select for donut charts)
     - Responses stored in `form_responses.demographics_json` object
     - Dashboard generates donut charts for each demographic dimension
     - Allows cross-filtering: view sentiment distribution within specific demographic groups
   - **Backend**: form_meta boolean flag, demographics_json in form_responses
   - **Data flow**: Admin enables demographics in builder → questions marked as demographic → responses collected → dashboard queries demographics_json → renders donut charts

---

## Step-by-Step User Flows

### **Flow 1: Create a Survey and Collect Feedback**

**Actors**: Transportation Agency Administrator

1. **Login**
   - Admin navigates to login page
   - Enters email and password
   - System validates credentials with Supabase
   - Session created and stored in database
   - Redirected to router/main app

2. **Create Form**
   - Admin clicks "New Form" in form builder
   - Form created with auto-generated form_id
   - Form defaults: "Untitled Form", no questions
   - Admin taken to form editor

3. **Configure Form Metadata**
   - Admin enters form title: "Service Quality Feedback - Bus Line 5"
   - Admin enters description: "Help us improve your experience"
   - Admin toggles "Include Demographics": YES
   - Admin sets "Allow Multiple Responses": YES (allows same user to fill multiple times)
   - Admin enters "Contact/Outreach Info": "noreply@transit.gov"
   - Admin clicks "Save Settings"

4. **Add Questions**
   - Admin clicks "Add Question"
   - Fills in question text: "How well-maintained are the vehicles?"
   - Selects question type: "Likert Scale (5-point)"
   - Assigns SERVQUAL dimension: "Tangibles"
   - Toggles "Enable Sentiment Analysis": YES (for text-based follow-ups only)
   - Marks as "Required": YES
   - Repeats for 8-10 more questions across all SERVQUAL dimensions
   - Adds demographic questions (e.g., "Age Group" as Multiple Choice)

5. **Preview Form**
   - Admin clicks "Preview Mode"
   - Sees form exactly as passengers will see it
   - Tests Likert scale interactions, text inputs
   - Verifies mobile responsiveness

6. **Generate Public Link**
   - Admin clicks "Get Sharing Link"
   - System displays: `https://transit-feedback.streamlit.app/?form_id=a1b2c3d4e5f6`
   - Admin copies link to clipboard
   - Admin shares link via:
     - Email campaign
     - QR code on bus interior posters
     - Social media
     - Website footer

7. **Passengers Submit Responses**
   - Passenger scans QR code or clicks link
   - Loads public form with form_id parameter
   - Sees form title and description
   - Fills out all required questions:
     - Rates tangibles: "4 - Good"
     - Rates reliability: "3 - Average"
     - Types comment on reliability: "Buses often run 5-10 mins late"
     - Selects age group: "25-34"
   - Clicks "Submit"
   - Response stored in form_responses table with:
     - responses_json: all answers
     - question_sentiments: {"reliability_comment": {"text": "Buses often run 5-10 mins late", "sentiment": "NEGATIVE"}}
     - demographics_json: {"age": "25-34"}
     - submitted_at: timestamp

8. **Admin Views Results on Dashboard**
   - Admin logs in, navigates to dashboard
   - Selects "Service Quality Feedback - Bus Line 5" from form dropdown
   - Dashboard loads with real-time data:
     - KPI: "127 responses collected"
     - KPI: "Average satisfaction: 3.4/5"
     - Sentiment chart: "Reliability dimension shows 45% Negative sentiment"
     - Demographic chart: "Ages 25-34 make up 32% of respondents"
   - Admin clicks on "Reliability" dimension
   - Dashboard filters to show:
     - Text comments tagged with Reliability + negative sentiment
     - Passenger demographics for negative feedback (mostly 25-34)
   - Admin generates report for transit authority leadership

**Duration**: 45 minutes setup + ongoing collection

---

### **Flow 2: Analyze Sentiment Across Models (Advanced)**

**Actors**: Data Scientist / Transit Quality Analyst

1. **Access Analysis Page**
   - User navigates to "Analysis" from sidebar
   - Sees three sections: Playground, Batch Upload, Model Comparison

2. **Playground Testing**
   - User pastes text: "The buses are always late and uncomfortable"
   - Clicks "Analyze"
   - Our model returns: **NEGATIVE** (confidence: 0.95)
   - Distribution shows: 95% NEGATIVE, 5% NEUTRAL, 0% POSITIVE

3. **Model Comparison Setup**
   - User clicks "Compare Models"
   - Selects baseline: "Twitter RoBERTa"
   - Pastes same text: "The buses are always late and uncomfortable"
   - Comparison panel shows:
     - **Our model** (Fine-tuned XLM-RoBERTa): NEGATIVE (0.95)
     - **Twitter RoBERTa**: NEGATIVE (0.91)
     - **Multilingual BERT**: NEGATIVE (0.88)
     - **DistilBERT**: NEGATIVE (0.87)
   - All models agree on classification
   - User notes: "Good consensus - models are reliable"

4. **Batch Upload for Validation**
   - User prepares CSV with 100 passenger comments (from previous survey)
   - Uploads file via "Batch Upload" section
   - System processes:
     - Reads CSV, extracts text column
     - Runs sentiment analysis on all 100 rows
     - Creates output CSV with original text + sentiment + confidence
   - Results downloaded:
     - 62 NEGATIVE, 24 NEUTRAL, 14 POSITIVE
     - Avg confidence: 0.82

5. **Insight Generation**
   - User analyzes distribution
   - Filters: Show only NEGATIVE comments
   - Reviews sample texts to find common themes:
     - "late" appears in 34/62 comments
     - "crowded" appears in 18/62 comments
   - Generates finding: "Top two pain points: Schedule adherence (55%) and Overcrowding (29%)"

**Duration**: 30 minutes for thorough comparison analysis

---

### **Flow 3: Respond to a Survey (End User/Passenger)**

**Actors**: Transit Passenger

1. **Access Survey**
   - Passenger receives notification/email with link or scans QR code at bus stop
   - Opens browser, clicks/scans link: `?form_id=a1b2c3d4e5f6`

2. **Load Form**
   - Page loads form with title: "Service Quality Feedback - Bus Line 5"
   - Sees description: "Help us improve your experience"
   - Sees questions rendered based on configuration

3. **Complete Survey**
   - Question 1 (Tangibles - Likert): Clicks on "4 - Good" button
   - Question 2 (Reliability - Likert): Clicks on "2 - Poor" button
   - Question 3 (Reliability - Text): Types: "Buses late 40% of the time, unacceptable"
   - Question 4 (Responsiveness - Multiple Choice): Selects "Average"
   - Question 5 (Demographic - Age Group): Selects "35-44"
   - Question 6 (Empathy - Text Area): Types longer comment about experience

4. **Submit Response**
   - Clicks "Submit Feedback"
   - System validates all required fields filled
   - Stores response in database:
     - Likert responses saved as numeric values
     - Text responses saved as strings
     - Sentiment analysis immediately triggered on text fields (if enabled)
   - Shows confirmation: "Thank you! Your feedback helps us improve."
   - Page reset for next respondent (if allow_multiple=true)

**Duration**: 3-5 minutes per respondent

---

## Technical Stack Summary

### **Frontend**
- **Framework**: Streamlit (Python web framework)
  - Reactive, no JavaScript needed
  - Session state management built-in
  - Pre-built UI components (text_input, radio, checkbox, etc.)
- **Styling**: Custom CSS injected via `st.markdown()`
  - CSS Variables for theme colors (navy, gold, steel, etc.)
  - Responsive design with media queries
  - Custom fonts: Libre Baskerville (serif), Mulish (sans-serif)
  - Component-specific CSS for Streamlit elements
- **Visualization Libraries**:
  - **Altair**: For bar charts, distribution visualizations
  - **Plotly**: For interactive charts (pie/donut, time-series)
  - **Pandas**: Data manipulation and aggregation

### **Backend**
- **Database**: Supabase (PostgreSQL + Firebase-style BaaS)
  - Tables:
    - `users` (from Supabase Auth)
    - `form_list` (form metadata)
    - `form_meta` (form settings, demographics config)
    - `form_questions` (question definitions)
    - `form_responses` (responses + sentiment analysis results)
    - `active_sessions` (user sessions with device fingerprinting)
  - Full-text search indexes on question_sentiments (JSONB GIN index)
  - Relationships: form_list → form_questions → form_responses
- **Authentication**: Supabase Auth
  - Email/password authentication
  - Session token management
  - User metadata storage

### **ML/NLP**
- **Transformers Library** (Hugging Face)
  - Model: `cardiffnlp/twitter-xlm-roberta-base-sentiment`
  - Multilingual sentiment classification (POSITIVE/NEUTRAL/NEGATIVE)
- **PyTorch**: Deep learning framework (CPU mode)
  - Installed from PyPI with CPU-only wheel
- **Tokenization**:
  - sentencepiece (for subword tokenization)
  - tiktoken (alternative tokenizer)

### **Key Dependencies**
- `streamlit` - Web framework
- `st-supabase-connection` - Supabase integration for Streamlit
- `supabase>=2.0.0` - Python Supabase client
- `pandas` - Data processing
- `transformers` - NLP models
- `torch` - Deep learning (CPU)
- `streamlit-extras` - Additional Streamlit components
- `extra-streamlit-components` - Custom components
- `openpyxl` - Excel file handling (for data export)
- `altair` - Visualization
- `plotly` - Interactive visualization
- `protobuf` - Data serialization (dependency)

### **Deployment Environment**
- Likely running on **Streamlit Cloud** or self-hosted Streamlit server
- Python 3.8+
- No separate REST API (Streamlit handles HTTP routing)
- Real-time updates via Streamlit's auto-rerun on parameter changes

### **Model Architecture Details**
- **XLM-RoBERTa** specifications:
  - 12-layer transformer
  - 768 hidden dimensions
  - Trained on 100+ languages
  - Fine-tuned on Twitter sentiment data
  - ~270M parameters
  - Inference time: ~50-100ms per text

---

## Other Notable Discoveries (The Catch-All)

### **1. SERVQUAL Framework Integration**
- The platform is specifically built around the **SERVQUAL model** (Service Quality Assessment)
- Five dimensions hardcoded in `servqual_utils.py`:
  - **Tangibles** (🚌): Physical evidence
  - **Reliability** (🕐): Consistent performance
  - **Responsiveness** (⚡): Willingness to help
  - **Assurance** (🛡️): Knowledge and courtesy
  - **Empathy** (🤝): Caring, individualized service
- Each question tagged with a dimension for thematic analysis
- Each dimension has unique color coding in dashboard for quick visual identification
- This is domain-specific for transportation service quality research (not generic survey tool)

---

### **2. Scale Normalization Engine**
- Function `normalize_to_5()` in dashboard.py automatically converts different rating scales:
  - 3-point scale → normalized to 0-5
  - 5-point scale → kept as-is
  - 10-point scale → divided by 2 to get 0-5 equivalent
  - Allows fair comparison across questions with different scales
  - Particularly useful for Likert scales varying in the form

---

### **3. Per-Question Sentiment Analysis**
- Advanced feature: Sentiment analysis runs **independently per question**, not on the entire response
- Each text field can have sentiment enabled/disabled individually
- Results stored in JSONB column `question_sentiments`:
  ```json
  {
    "q_reliability_comments": {"text": "...", "enable_sentiment": true, "sentiment": "NEGATIVE"},
    "q_name": {"text": "...", "enable_sentiment": false, "sentiment": null}
  }
  ```
- Allows granular analysis: e.g., "Only analyze text on Reliability dimension, ignore demographic fields"
- GIN index on this column enables fast queries like "find all responses with negative reliability sentiment"

---

### **4. Device Fingerprinting & Session Tracking**
- Login process generates `device_id` from User-Agent header (MD5 hash)
- Sessions stored in `active_sessions` table with:
  - `session_id` (UUID)
  - `user_email`
  - `device_id`
  - `login_time`
- Enables detection of multi-device access
- Could support features like "logout all other sessions" or "suspicious login alerts"
- Currently integrated but not heavily used in visible UI

---

### **5. Legacy Form Migration Logic**
- Backward compatibility function: `get_legacy_form_id(admin_email)`
- Generates form_id from email hash (MD5)
- Used to migrate single-form users to multi-form system
- Single-form users transitioned transparently without data loss
- Modern system uses UUID-based form IDs for new users

---

### **6. Dynamic Shareable Link Generation**
- Public form links generated dynamically based on request context:
  ```python
  host = st.context.headers.get("Host")
  protocol = "https" if "localhost" not in host else "http"
  base_url = f"{protocol}://{host}"
  shareable_link = f"{base_url}/?form_id={public_id}"
  ```
- Automatically detects if running locally (http) or deployed (https)
- Works across different deployment environments without hardcoding URLs
- Form ID passed as query parameter (not URL path) for simplicity

---

### **7. Responsive Mobile-First Design**
- Login page: Hidden left branding panel on mobile (<992px)
- Public form: Centered, max-width 760px
- Dashboard: Adaptive grid layout
- Form builder: Responsive multi-column layouts
- Extensive media queries for different breakpoints
- Custom CSS ensures Streamlit native components fit mobile UX

---

### **8. Demographic-Constrained Question Types**
- Demographics section only accepts **Multiple Choice** or **Multiple Select** question types
- Reason: Donut charts require discrete categories, not continuous text/ratings
- Validation in builder: `demographic_qtype_ok()` function checks if question type compatible
- Prevents admin from creating demographic questions that can't be visualized

---

### **9. Form Archival System (Soft Delete)**
- Forms never permanently deleted; instead marked `is_archived = true` in database
- Archived forms:
  - Hidden from main form list by default
  - Can be viewed/restored from "Archived Forms" tab
  - All historical responses preserved
  - Reduces accidental data loss
- Soft-delete pattern enables audit trails and recovery

---

### **10. Dual Sentiment Comparison Modes**
- **Playground mode**: Single-text analysis with instant feedback
- **Batch mode**: CSV upload for bulk processing
  - Useful for analyzing historical data or comparing models
  - Returns downloadable CSV with sentiment added to each row
  - Enables benchmarking against previous surveys

---

### **11. Multiple Model Comparison with Label Normalization**
- Baseline models have different output formats:
  - RoBERTa: `LABEL_0`, `LABEL_1`, `LABEL_2` (0=negative, 1=neutral, 2=positive)
  - BERT stars: Star ratings (1-5) mapped to negative/neutral/positive
  - DistilBERT: Binary classification (NEGATIVE/POSITIVE) with neutral inferred from confidence
- Function `normalize_comparison_prediction()` intelligently maps all formats to standard: **POSITIVE | NEUTRAL | NEGATIVE**
- Allows fair comparison despite different model architectures and training data

---

### **12. Confidence Scoring**
- All sentiment predictions include confidence score (0-1)
- Confidence indicates model certainty
- Dashboard displays confidence alongside sentiment label
- Batch export includes confidence for filtering low-confidence predictions
- Useful for identifying ambiguous text that humans should review

---

### **13. Streaming and Real-Time Updates**
- Dashboard auto-reruns when:
  - Form selection changes
  - Time filter changes
  - Demographic filter changes
- No manual refresh needed
- Streamlit's reactive model automatically triggers Supabase queries
- May create performance bottleneck with large datasets (1000+ responses)

---

### **14. CSS Color System**
- Comprehensive CSS variable system for consistent theming:
  - `--navy` (primary): #1a3263
  - `--gold` (accent): #ffc570
  - `--steel` (secondary): #547792
  - `--pos` (positive sentiment): #4a7c59 (green)
  - `--neg` (negative sentiment): #b03a2e (red)
  - `--neu` (neutral sentiment): #8b9dc3 (muted blue)
- All colors defined in `:root` CSS block
- Easy theme swaps by changing variable values
- Dimension colors follow same pattern with unique hex codes

---

### **15. Hidden Streamlit Native UI**
- All pages explicitly hide:
  - `#MainMenu` - hamburger menu
  - `footer` - "Made with Streamlit"
  - `[data-testid="stToolbar"]` - Settings/info buttons
  - `[data-testid="stStatusWidget"]` - Rerun status
  - `[data-testid="stDecoration"]` - Watermark
- Creates seamless branded experience (users don't know it's Streamlit)
- Sidebar managed manually via st.sidebar and custom CSS

---

### **16. Preview Mode in Form Builder**
- Builder has toggle for "Preview Mode"
- When enabled, shows form exactly as respondents see it
- Allows admin to test:
  - Likert scale interaction
  - Multiple choice rendering
  - Text input/area behavior
  - Mobile responsiveness
  - Demographic section (if enabled)
- Non-functional preview (no data saved)
- Critical for QA before public deployment

---

### **17. Form Metadata Upsert Pattern**
- When form created in `form_list` table, corresponding entry auto-created in `form_meta`
- Uses Supabase `.upsert()` with `on_conflict` clause
- Ensures form always has settings even if admin doesn't configure them explicitly
- Defaults:
  - `include_demographics` = false
  - `allow_multiple_responses` = true
  - `reach_out_contact` = empty string

---

### **18. Client Submission ID Tracking**
- Each form response stores unique `client_submission_id`
- Enables tracking of unique respondents even on mobile (no cookies)
- Could be:
  - Device ID
  - Session ID
  - IP address + User-Agent hash
  - Or explicitly provided by respondent
- Used to prevent duplicate submissions (when `allow_multiple_responses=false`)

---

### **19. JSONB Flexibility for Future Extensibility**
- Responses stored as flexible JSON objects:
  - `responses_json`: All question answers
  - `demographics_json`: Demographic data
  - `question_sentiments`: Sentiment analysis results
- Allows adding new question types without schema migration
- Admin can add custom fields without code changes
- Makes system future-proof and adaptable

---

### **20. Model Auto-Loading on First Use**
- Transformers library downloads model on first inference call (lazy loading)
- Model cached locally after first download (~500MB for XLM-RoBERTa)
- Subsequent calls use cached model (fast inference)
- Cold start on first request may be slow (5-10 seconds)
- Subsequent requests ~100ms each
- Not explicitly shown in code but implied by transformers behavior

---

## Summary Statistics

| Aspect | Value |
|--------|-------|
| **Total Pages** | 7 (Login, Router, Builder, Public Form, Dashboard, Analysis, Settings) |
| **SERVQUAL Dimensions** | 5 (Tangibles, Reliability, Responsiveness, Assurance, Empathy) |
| **Question Types** | 6 (Multiple Choice, Multiple Select, Likert Scale, Text, Textarea, Rating) |
| **Sentiment Classes** | 3 (POSITIVE, NEUTRAL, NEGATIVE) |
| **Comparison Baseline Models** | 3 (Twitter RoBERTa, Multilingual BERT, DistilBERT) |
| **Core Supabase Tables** | 6+ (users, form_list, form_meta, form_questions, form_responses, active_sessions) |
| **Visualization Libraries** | 2 (Altair, Plotly) |
| **CSS Custom Properties** | 15+ (navy, gold, steel, pos, neg, neu, tangibles, reliability, etc.) |
| **Authentication Method** | Supabase Auth (Email/Password) |
| **Device Tracking** | Via MD5 hash of User-Agent |

---

## Conclusion

This is a **specialized sentiment analysis platform for transportation agencies**, combining survey collection, real-time analytics, and machine learning classification into a polished, accessible web interface. The platform leverages SERVQUAL framework theory with modern ML sentiment analysis to transform qualitative feedback into quantitative insights. Every design choice—from color coding to mobile optimization to flexible JSONB storage—reflects careful consideration for both administrative users (who build and interpret) and end users (who respond).

The technical architecture is elegant: Streamlit + Supabase for simplicity, Transformers for ML, and extensive custom CSS for branding. The system scales from small transit agencies (100s of responses) to larger operations (1000s) with reasonable performance, though real-time dashboards with 10,000+ responses may require optimization (pagination, caching, or aggregation tables).

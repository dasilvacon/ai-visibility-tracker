# AI Visibility Tracker

A Python-based tool for testing prompts across multiple AI platforms and tracking visibility scores. Compare how different AI models respond to your prompts and analyze their performance.

## Features

- **AI-Powered Prompt Generation**: Automatically generate hundreds or thousands of natural, realistic prompts
- **Persona-Based Distribution**: Create prompts based on user personas and priority topics
- **Keyword Integration**: Use SEO keywords and competitor data to generate relevant queries
- **Multi-Platform Testing**: Test prompts across multiple AI platforms (OpenAI, Anthropic Claude, and more)
- **CSV-Based Management**: Easy-to-use prompts database and keyword management
- **Comprehensive Tracking**: Results tracked with JSON and CSV output
- **Automated Reporting**: Performance metrics and platform comparisons
- **Modular Design**: Easy platform additions and customization
- **Secure Configuration**: API key management via config files

## Project Structure

```
ai-visibility-tracker/
├── config/
│   └── config.template.json    # Configuration template
├── data/
│   ├── prompts_template.csv    # Sample prompts database
│   ├── personas_template.json  # Sample persona definitions
│   ├── keywords_template.csv   # Sample keywords for generation
│   ├── results/                # Test results (auto-generated)
│   └── reports/                # Generated reports (auto-generated)
├── src/
│   ├── api_clients/            # API client implementations
│   │   ├── base_client.py      # Base class for all clients
│   │   ├── openai_client.py    # OpenAI integration
│   │   └── anthropic_client.py # Anthropic integration
│   ├── database/               # Database management
│   │   └── prompts_db.py       # Prompts CSV manager
│   ├── prompt_generator/       # Prompt generation module
│   │   ├── generator.py        # Main generation engine
│   │   ├── persona_manager.py  # Persona definitions manager
│   │   ├── keyword_processor.py # Keyword data processor
│   │   └── prompt_builder.py   # Natural query builder
│   ├── tracking/               # Results tracking
│   │   └── results_tracker.py  # Results logger
│   └── reporting/              # Report generation
│       └── report_generator.py # Report builder
├── tests/                      # Unit tests (future)
├── main.py                     # Main runner script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- API keys for desired platforms:
  - OpenAI API key
  - Anthropic API key
  - (Future: Perplexity, DeepSeek, Grok)

### 2. Installation

1. Clone or navigate to the project directory:
```bash
cd ai-visibility-tracker
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration

1. Copy the configuration template:
```bash
cp config/config.template.json config/config.json
```

2. Edit `config/config.json` and add your API keys:
```json
{
  "api_keys": {
    "openai": "sk-your-openai-key-here",
    "anthropic": "sk-ant-your-anthropic-key-here"
  },
  "models": {
    "openai": "gpt-4",
    "anthropic": "claude-3-5-sonnet-20241022"
  }
}
```

Note: `config/config.json` is gitignored to protect your API keys.

### 4. Prepare Your Prompts

The prompts database is a CSV file with the following schema:

- `prompt_id`: Unique identifier for the prompt
- `persona`: User persona (e.g., data_scientist, business_analyst)
- `category`: Category of the prompt (e.g., technical, business)
- `intent_type`: Type of intent (e.g., information_seeking, analysis)
- `prompt_text`: The actual prompt text
- `expected_visibility_score`: Expected score (1-10)
- `notes`: Additional notes

You can use the provided `data/prompts_template.csv` as a starting point or create your own.

## Usage

### Basic Usage

Run tests with default settings:
```bash
python main.py
```

### Advanced Options

Specify a custom configuration file:
```bash
python main.py --config path/to/config.json
```

Use a custom prompts file:
```bash
python main.py --prompts path/to/prompts.csv
```

Test on specific platforms only:
```bash
python main.py --platforms openai anthropic
```

Generate reports only (from existing results):
```bash
python main.py --report-only
```

### Full Example

```bash
python main.py --config config/config.json \
               --prompts data/my_prompts.csv \
               --platforms openai anthropic
```

## Prompt Generation

The AI Visibility Tracker includes a powerful prompt generation module that can automatically create realistic, natural prompts for testing brand visibility. Instead of manually creating prompts, you can generate hundreds or thousands of diverse prompts based on personas and keywords.

### How It Works

The prompt generator:
1. **Loads persona definitions** from a JSON file (user types, behaviors, needs)
2. **Processes keyword data** from a CSV file (search terms, intent types, competitors)
3. **Uses AI APIs** (OpenAI or Anthropic) to generate natural, conversational variations
4. **Distributes prompts** across personas based on defined weights
5. **Creates diverse query types**: questions, comparisons, how-tos, problem-solving
6. **Includes competitor mentions** in ~30% of prompts for comparison testing

### Input Files

#### 1. Personas File (`personas_template.json`)

Defines user personas with weights and priority topics:

```json
{
  "personas": [
    {
      "id": "new_parent",
      "name": "New Parent Caregiver",
      "description": "First-time parents caring for newborns...",
      "weight": 0.30,
      "priority_topics": ["sleep training", "feeding schedules"]
    }
  ]
}
```

The template includes 5 sample personas:
- New Parent Caregiver (30%)
- Health-Conscious Adult (25%)
- Small Business Owner (20%)
- Tech Professional (15%)
- Home Improvement DIY Enthusiast (10%)

#### 2. Keywords File (`keywords_template.csv`)

Defines keywords with search volume, intent, and competitors:

```csv
keyword,search_volume,intent_type,competitor_brands
how to sleep train baby,8500,how_to,"Huckleberry,Nested Bean,Owlet"
best baby monitor 2024,12000,recommendation,"Nanit,Infant Optics"
```

The template includes 25 sample keywords across different categories.

### Generating Prompts

#### Basic Generation

Generate 100 prompts using AI:
```bash
python main.py --generate-prompts --count 100
```

#### Custom Input Files

Use your own personas and keywords:
```bash
python main.py --generate-prompts \
               --personas data/my_personas.json \
               --keywords data/my_keywords.csv \
               --output data/my_generated_prompts.csv \
               --count 1000
```

#### Template-Based Generation (No AI)

Generate prompts without using AI APIs (uses templates only):
```bash
python main.py --generate-prompts --no-ai --count 100
```

#### Full Pipeline: Generate + Test

Generate prompts and immediately test them:
```bash
python main.py --full-pipeline \
               --count 500 \
               --platforms openai anthropic
```

This will:
1. Generate 500 prompts
2. Save them to `data/generated_prompts.csv`
3. Run visibility tests on all generated prompts
4. Generate reports

### Output Files

When you generate prompts, the system creates:

1. **Generated Prompts CSV** (`data/generated_prompts.csv`):
   - Matches the standard prompts database format
   - Can be used directly with the visibility tracker
   - Includes: prompt_id, persona, category, intent_type, prompt_text, expected_visibility_score, notes

2. **Generation Summary Report** (`data/generated_prompts_summary.txt`):
   - Breakdown by persona
   - Breakdown by category and intent type
   - Statistics on competitor mentions
   - Sample prompts
   - Generation time

### Example Generated Prompts

The AI generates natural, realistic queries like:

- "I'm a new parent and my 4-month-old won't sleep through the night. Any advice on sleep training methods that actually work?"
- "Looking for the best baby monitor for 2024. How does Nanit compare to Infant Optics?"
- "Quick question: what's the difference between meal prep and meal planning for weight loss?"
- "Hey, I need help with social media marketing for my small business. What tools do you recommend?"

### Customizing Personas and Keywords

1. **Create Your Personas**: Copy `data/personas_template.json` and modify:
   - Add personas relevant to your brand/product
   - Adjust weights to match your target audience distribution
   - Define priority topics that matter to each persona

2. **Create Your Keywords**: Copy `data/keywords_template.csv` and add:
   - Keywords from your SEO research
   - Search volumes from keyword tools
   - Intent types (informational, how_to, comparison, etc.)
   - Your actual competitors

3. **Run Generation**: Use your custom files to generate prompts

### Best Practices

- **Start small**: Test with 50-100 prompts first to validate quality
- **Review samples**: Check the generated prompts before running tests
- **Use AI generation**: AI-generated prompts are more natural than templates
- **Mix personas**: Ensure persona weights reflect your real audience
- **Include competitors**: Add competitor mentions to test comparative visibility
- **Iterate**: Refine your personas and keywords based on results

## Output

### Results

Test results are stored in two formats:

1. **JSON files** (`data/results/test_*.json`): Full detailed results for each test
2. **CSV summary** (`data/results/results_summary.csv`): Aggregated summary of all tests

### Reports

Reports are generated in `data/reports/`:

1. **Summary Report**: Overall statistics, platform breakdown, performance metrics
2. **Platform Comparison**: Side-by-side comparison of how each platform performed on each prompt

## Adding New Platforms

The project is designed for easy extensibility. To add a new platform:

1. Create a new client class in `src/api_clients/` that inherits from `BaseAPIClient`
2. Implement the required methods:
   - `_get_platform_name()`
   - `send_prompt()`
3. Add the platform to the configuration template
4. Initialize the client in `main.py`

Example structure:
```python
from .base_client import BaseAPIClient

class NewPlatformClient(BaseAPIClient):
    def _get_platform_name(self) -> str:
        return 'newplatform'

    def send_prompt(self, prompt, temperature=None, max_tokens=None):
        # Implementation here
        pass
```

## Prompts Database Management

### Adding Prompts

You can add prompts directly to the CSV file or use the PromptsDatabase API:

```python
from src.database.prompts_db import PromptsDatabase

db = PromptsDatabase('data/prompts_template.csv')
db.add_prompt({
    'prompt_id': '6',
    'persona': 'researcher',
    'category': 'academic',
    'intent_type': 'research',
    'prompt_text': 'What are the latest developments in quantum computing?',
    'expected_visibility_score': 8.0,
    'notes': 'Current events query'
})
```

### Filtering Prompts

```python
# Filter by persona
scientist_prompts = db.filter_prompts(persona='data_scientist')

# Filter by category
technical_prompts = db.filter_prompts(category='technical')

# Multiple filters
specific_prompts = db.filter_prompts(
    persona='business_analyst',
    category='business'
)
```

## Results Analysis

### Loading Results

```python
from src.tracking.results_tracker import ResultsTracker

tracker = ResultsTracker('data/results')

# Load all results
all_results = tracker.load_results_summary()

# Load results for specific platform
openai_results = tracker.get_results_by_platform('openai')

# Load results for specific prompt
prompt_results = tracker.get_results_by_prompt('1')
```

## Development

### Running Tests

(To be implemented)
```bash
pytest tests/
```

### Code Formatting

```bash
black src/ main.py
```

### Linting

```bash
pylint src/ main.py
```

## License

This project is provided as-is for personal and educational use.

## Contributing

To contribute or suggest improvements, please create an issue or pull request.

## Support

For questions or issues, please refer to the documentation or create an issue in the project repository.

## Roadmap

- [ ] Add support for Perplexity AI
- [ ] Add support for DeepSeek
- [ ] Add support for Grok
- [ ] Implement automated visibility scoring
- [ ] Add visualization dashboards
- [ ] Add unit tests
- [ ] Add batch processing for large prompt sets
- [ ] Add retry logic for failed API calls
- [ ] Add rate limiting support
- [ ] Add cost tracking per platform

# ChainForge AutoEval

This project provides an automated evaluation workflow using ChainForge with custom providers for OR Assistant and Gemini 1.5 Pro.

## Installation

1. Install ChainForge:

   ```
   pip install chainforge
   ```

## Usage

1. Set up your API keys:

   - For OR Assistant: No API key required
   - For Gemini 1.5 Pro: Set your API key in the ChainForge UI

2. Run the evaluation workflow:

   ```
   chainforge run evaluation_workflow.cforge
   ```

3. View the results in the ChainForge UI

## Custom Providers

This project includes two custom providers:

1. OR Assistant (`Or Assistant.py`)
2. Gemini 1.5 Pro (`Gemini 1.5 Pro Wrapper.py`)

These providers are automatically loaded by ChainForge when running the evaluation workflow.


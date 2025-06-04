import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const { latestQuestion, assistantAnswer } = await request.json();
  const prompt = `If the assistant answer has sufficient knowledge, use it to predict the next 3 suggested questions. Otherwise, strictly restrict to these topics: Given the list of topics related to OpenROAD, suggest 3 relevant questions strictly focused on any of the given topics.
  Getting Started with OpenROAD
  Building OpenROAD
  Getting Started with the OpenROAD Flow - OpenROAD-flow-scripts
  Tutorials
  Git Quickstart
  Man pages
  OpenROAD User Guide
  Database
  GUI
  Partition Management
  Restructure
  Floorplan Initialization
  Pin Placement
  Chip-level Connections
  Macro Placement
  Hierarchical Macro Placement
  Tapcell Insertion
  PDN Generation
  Global Placement
  Gate Resizing
  Detailed Placement
  Clock Tree Synthesis
  Global Routing
  Antenna Checker
  Detailed Routing
  Metal Fill
  Parasitics Extraction
  Messages Glossary
  Getting Involved
  Developer's Guide
  Coding Practices
  Logger
  CI
  README Format
  Tcl Format
  Man pages Test Framework
  Code of Conduct
  FAQs

  Your response must be in this exact JSON format:
  {
    "questions": [
      "",
      "",
      ""
    ]
  }
  The first character should be '{' and the last character should be '}'. Do not include any additional text or formatting.`;

  try {
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${process.env.GEMINI_API_KEY}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                {
                  text: `${prompt}\n\nUser Question: ${latestQuestion}\n\nAssistant Answer: ${assistantAnswer}`,
                },
              ],
            },
          ],
        }),
      }
    );

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in API route:', error);
    return NextResponse.json(
      { error: 'An error occurred while processing your request' },
      { status: 500 }
    );
  }
}

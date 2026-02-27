Rock-Paper-Scissors Service

Overview

This is a web microservice that provides web page interaction for the rock-paper-scissors game. The service returns HTML pages (not JSON).

Service Information

- Running port (default): 5000
- Base URL: `http://127.0.0.1:5000`

API Definition

- API Name: Homepage
  - Method: GET
  - Path: `/`
  - Input: None
  - Output: HTML document containing title "Rock-Paper-Scissors App", `<form action="/results" method="POST">`, form field `choice` (value enum: `rock`, `paper`, `scissors`).

- API Name: Results page (query parameters)
  - Method: GET
  - Path: `/results`
  - Input Schema:
    - `choice` (query): string, enum {`rock`,`paper`,`scissors`}. When not provided or invalid value is provided, service treats as `rock`.
  - Output: HTML document containing the following text segments:
    - `You chose: <user_choice>`
    - `The computer chose: <computer_choice>`
    - `Results: <message>`

- API Name: Results page (form)
  - Method: POST
  - Path: `/results`
  - Input Schema:
    - `choice` (form): string, enum {`rock`,`paper`,`scissors`}. When not provided or invalid value is provided, service treats as `rock`.
  - Output: Same as GET `/results`.

Input/Output Schema Summary

- Input parameter `choice`:
  - Type: string
  - Location: query (GET) or form (POST)
  - Constraints: Must be one of `rock`, `paper`, `scissors`; otherwise treated as `rock`
- Output document: HTML containing three key text lines ("You chose:", "The computer chose:", "Results:").

Local Running (Informational)

- Environment variable `FLASK_APP=web_app`, or other similar frameworks
- Listen on `:5000` (or external gateway specified port).

Testing Conventions

- Tests call HTTP interfaces in black-box manner, based on `SERVICE_BASE_URL` environment variable (default `http://127.0.0.1:5000`).




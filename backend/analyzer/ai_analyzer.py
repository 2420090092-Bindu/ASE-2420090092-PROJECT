import os
from groq import Groq


def analyze_patch(changed_functions, dependency_map):

    # Get Groq API key
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return {
            "error": "GROQ_API_KEY is not set."
        }

    # Create Groq client
    client = Groq(api_key=api_key)

    # Create prompt
    prompt = f"""
You are an expert software security patch impact analyzer.

Your job is to determine the risk level of a software patch
STRICTLY from the changes provided below.

CHANGED FUNCTIONS:
{changed_functions}

DEPENDENCY MAP:
{dependency_map}


==================================================
RISK CLASSIFICATION RULES
==================================================

You MUST follow these rules carefully.

LOW:
Choose LOW when the patch is harmless and mainly additive.

Examples:
- Adding a new independent function
- Adding a helper function that does not affect existing functions
- Adding a version function
- Adding logging that does not change application behavior
- Adding comments or documentation
- Adding functionality with no important existing dependencies
- Changes that are unlikely to break existing functionality

If there are only simple additions and no existing functions
are removed or significantly modified, strongly prefer LOW.


MEDIUM:
Choose MEDIUM when the patch changes existing functionality
but the impact is limited.

Examples:
- Modifying an existing function
- Changing normal application logic
- Changing a function that has a small number of dependents
- Changing non-security-related behavior
- Removing a function that has limited dependencies
- Changes that could cause functional regressions but are
  unlikely to create a serious security vulnerability


HIGH:
Choose HIGH when the patch can cause significant functional
or security impact.

Examples:
- Removing important functions that other functions depend on
- Modifying several existing functions
- Changes affecting many dependent functions
- Changes to authentication, authorization, input validation,
  encryption, database access, file handling, or security checks
- Changes that can cause major application failure
- Changes that could introduce a significant security weakness


CRITICAL:
Choose CRITICAL ONLY when the patch creates or removes
extremely important security controls or can cause severe
security consequences.

Examples:
- Authentication bypass
- Authorization bypass
- Privilege escalation
- Exposure of highly sensitive data
- Disabling a major security mechanism
- Removing critical security validation
- Changes that could compromise the entire application


==================================================
IMPORTANT DECISION RULES
==================================================

1. Do NOT automatically choose MEDIUM.

2. If the patch only adds an independent harmless function,
   choose LOW.

3. If existing functions are modified, do NOT choose LOW
   unless the modification is clearly harmless.

4. If important existing functions are removed,
   consider HIGH or CRITICAL depending on their security impact.

5. The number of changed functions alone does NOT determine
   the risk level.

6. Dependencies are very important.
   A function with many dependents has greater impact than
   an independent function.

7. Security-related functions must receive higher risk
   when their security behavior is changed or removed.

8. Do not invent functions, files, modules, dependencies,
   vulnerabilities, or security problems.

9. Use ONLY the information provided in CHANGED FUNCTIONS
   and DEPENDENCY MAP.

10. Choose exactly ONE risk level:
    LOW
    MEDIUM
    HIGH
    CRITICAL


==================================================
OUTPUT FORMAT
==================================================

Provide the analysis using EXACTLY these sections:

1. Risk Level
2. Affected Modules
3. Possible Side Effects
4. Testing Suggestions


For Risk Level:

Write the level first, followed by a short explanation.

Example:

LOW – The patch only adds an independent function and does
not modify or remove existing functionality.


For Affected Modules:

List the files, functions, classes, or modules affected by
the patch.

For Possible Side Effects:

Explain realistic functional or security side effects.

For Testing Suggestions:

Give practical tests that developers should perform.

Keep the analysis concise and specific.

Do not invent information.
"""

    try:

        # Send request to Groq
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict software security "
                        "patch impact analyzer. Follow the "
                        "risk classification rules exactly."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        # Get AI response
        ai_text = response.choices[0].message.content

        return {
            "ai_analysis": ai_text
        }

    except Exception as e:

        return {
            "error": str(e)
        }
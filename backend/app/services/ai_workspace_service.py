import json
from typing import Optional


class AIWorkspaceService:
    _TASK_CONFIGS = {
        "video_analyze": {
            "category": "DAILY",
            "default_return": {"suggestions": [], "auto_edit_plan": {"steps": []}, "style_analysis": {}},
        },
        "generate_subtitles": {
            "category": "MEMORY",
            "default_return_factory": lambda language: {"subtitles": [], "language": language, "total_segments": 0},
        },
        "document": {
            "action_prompts": {
                "summarize": "Summarize the following document content concisely.",
                "expand": "Expand and elaborate on the following content with more detail.",
                "rewrite": "Rewrite the following content to improve clarity and flow.",
                "translate": "Translate the following content. Return JSON: {translated, source_lang, target_lang}.",
                "grammar": "Check and fix grammar issues. Return JSON: {corrected, issues: [{original, corrected, type}]}.",
                "outline": "Generate a structured outline for a document based on the topic. Return JSON: {outline: [{text, level}]}.",
                "tone_adjust": "Adjust the tone of the content. Return JSON: {adjusted, tone_description}.",
                "continue_writing": "Continue writing from where the text ends. Maintain the same style, tone, and context. Return JSON: {continuation}.",
                "qa": "Answer questions about the document content based on the provided context. Return JSON: {answer, sources, confidence}.",
            },
            "default_prompt": "Assist with the following document content.",
            "suffix": " Return JSON with the result.",
            "category": "DAILY",
            "category_overrides": {"outline": "PLANNING", "qa": "PLANNING"},
            "default_return": {"result": ""},
        },
        "ppt": {
            "action_prompts": {
                "generate_slides": "Generate slide content for a presentation. Return JSON: {slides: [{title, bullets, notes, layout_suggestion}]}.",
                "improve_slide": "Improve the content of a specific slide. Return JSON: {improved_title, improved_bullets, suggestions}.",
                "suggest_design": "Suggest visual design for slides. Return JSON: {color_scheme, font_suggestions, layout_tips, image_suggestions}.",
                "add_speaker_notes": "Generate speaker notes for slides. Return JSON: {notes}.",
                "summarize_presentation": "Summarize the entire presentation. Return JSON: {summary, key_points, duration_estimate}.",
                "outline_to_slides": "Convert the given outline or existing content into a structured slide deck. Return JSON: {slides: [{title, bullets, notes, layout_suggestion}]}.",
                "expand_content": "Expand and elaborate the slide content with more detail and supporting points. Return JSON: {improved_title, improved_bullets, suggestions}.",
                "condense_content": "Condense the slide content to be more concise and impactful. Return JSON: {improved_title, improved_bullets, suggestions}.",
                "translate": "Translate the slide content to the target language. Return JSON: {translated, source_lang, target_lang}.",
                "tone_adjust": "Adjust the tone of the slide content. Return JSON: {adjusted, adjusted_bullets, tone_description}.",
                "smart_layout": "Analyze the slides and recommend optimal layouts for each. Return JSON: {recommended_layouts: [{slide_index, recommended_layout, reason}], overall_assessment}.",
                "image_suggest": "Suggest images or visual elements for the slide. Return JSON: {image_suggestions: [{description, placement, style}], visual_metaphors}.",
                "coaching": "Provide presentation delivery coaching tips based on the slide content. Return JSON: {coaching_tips: [string], pacing_advice, engagement_strategies}.",
                "check_consistency": "Check the presentation for style and content consistency. Return JSON: {consistency_issues: [{severity, description, slide_index, suggestion}], overall_score}.",
                "audience_analysis": "Analyze the presentation for target audience suitability. Return JSON: {audience_insights, recommended_adjustments, engagement_score}.",
                "timing_estimate": "Estimate the presentation duration and pacing. Return JSON: {total_minutes, per_slide_estimates: [{slide_index, minutes}], pacing_recommendations}.",
            },
            "default_prompt": "Assist with the presentation.",
            "category": "PLANNING",
            "category_overrides": {"translate": "DAILY", "timing_estimate": "DAILY", "condense_content": "DAILY"},
            "default_return": {"result": ""},
        },
        "excel": {
            "action_prompts": {
                "analyze_data": "Analyze the spreadsheet data and provide insights. Return JSON: {insights, trends, anomalies, recommendations}.",
                "suggest_formula": "Suggest Excel formulas for the given requirement. Return JSON: {formulas: [{formula, description, cell_range}]}.",
                "generate_chart": "Suggest the best chart type and configuration. Return JSON: {chart_type, config, data_range, title_suggestion}.",
                "clean_data": "Suggest data cleaning operations. Return JSON: {operations: [{type, description, affected_range}]}.",
                "forecast": "Generate forecast based on historical data. Return JSON: {method, forecast_values, confidence_interval}.",
            },
            "default_prompt": "Assist with the spreadsheet.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "calendar": {
            "action_prompts": {
                "schedule": "Suggest an optimal schedule. Return JSON: {events: [{title, start, end, priority, reason}]}.",
                "conflict_resolve": "Resolve scheduling conflicts. Return JSON: {resolution, alternatives}.",
                "smart_reminder": "Suggest smart reminder settings. Return JSON: {reminders: [{event, time_before, type, reason}]}.",
                "time_estimate": "Estimate time needed for tasks. Return JSON: {estimates: [{task, hours, confidence, factors}]}.",
            },
            "default_prompt": "Assist with calendar management.",
            "category": "INTENT",
            "default_return": {"result": ""},
        },
        "knowledge": {
            "action_prompts": {
                "semantic_search": "Perform semantic search across knowledge base. Return JSON: {results: [{title, relevance, snippet}]}.",
                "summarize_doc": "Summarize the document. Return JSON: {summary, key_points, entities, topics}.",
                "auto_tag": "Auto-tag the document. Return JSON: {tags: [{name, confidence, category}]}.",
                "qa": "Answer questions based on the knowledge base. Return JSON: {answer, sources, confidence}.",
                "extract_entities": "Extract named entities. Return JSON: {entities: [{name, type, count}]}.",
            },
            "default_prompt": "Assist with knowledge management.",
            "category": "MEMORY",
            "category_overrides": {"qa": "PLANNING"},
            "default_return": {"result": ""},
        },
        "todo": {
            "action_prompts": {
                "prioritize": "Prioritize tasks intelligently. Return JSON: {ordered_tasks: [{id, priority, reason}], suggestions}.",
                "decompose": "Break down a complex task into subtasks. Return JSON: {subtasks: [{title, estimate, dependencies}]}.",
                "estimate": "Estimate time for tasks. Return JSON: {estimates: [{task, hours, confidence}]}.",
                "suggest_next": "Suggest the next best task to work on. Return JSON: {task_id, reason, context_match}.",
            },
            "default_prompt": "Assist with task management.",
            "category": "INTENT",
            "default_return": {"result": ""},
        },
        "email": {
            "action_prompts": {
                "compose": "Compose a professional email. Return JSON: {subject, body, tone}.",
                "reply": "Generate a reply to the email. Return JSON: {body, tone, suggested_action}.",
                "summarize": "Summarize the email thread. Return JSON: {summary, action_items, key_decisions}.",
                "categorize": "Categorize the email. Return JSON: {category, urgency, suggested_folder}.",
            },
            "default_prompt": "Assist with email.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "memo": {
            "action_prompts": {
                "categorize": "Categorize the memo into appropriate categories. Return JSON: {category, subcategories, confidence}.",
                "summarize": "Summarize the memo content concisely. Return JSON: {summary, key_points, action_items}.",
                "expand": "Expand the memo with more detail and structure. Return JSON: {expanded_content, added_sections}.",
                "extract_tasks": "Extract actionable tasks from the memo. Return JSON: {tasks: [{title, priority, due_hint}]}.",
                "suggest_title": "Suggest a concise title for the memo. Return JSON: {titles: [{text, confidence}]}.",
            },
            "default_prompt": "Assist with memo.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "kanban": {
            "action_prompts": {
                "suggest_progress": "Analyze the kanban board progress and suggest improvements. Return JSON: {progress_analysis, bottlenecks, suggestions: [{type, description, priority}]}.",
                "auto_assign": "Suggest optimal task assignments based on workload. Return JSON: {assignments: [{card_id, suggested_assignee, reason}]}.",
                "estimate_completion": "Estimate project completion timeline. Return JSON: {estimated_date, confidence, factors, risks}.",
                "prioritize_cards": "Prioritize cards across columns. Return JSON: {ordered_cards: [{card_id, priority, reason}]}.",
            },
            "default_prompt": "Assist with kanban board.",
            "category": "INTENT",
            "default_return": {"result": ""},
        },
        "recorder": {
            "action_prompts": {
                "summarize_recording": "Summarize the screen recording content based on key frames and metadata. Return JSON: {summary, key_points, topics, duration_estimate}.",
                "extract_highlights": "Extract highlight moments from the recording based on key frames. Return JSON: {highlights: [{timestamp, description, importance}]}.",
                "suggest_title": "Suggest a title for the recording based on key frames. Return JSON: {titles: [{text, confidence}]}.",
                "generate_chapters": "Generate chapter markers for the recording based on key frames. Return JSON: {chapters: [{title, start_time, description}]}.",
                "extract_text": "Extract all visible text from the recording key frames. Return JSON: {text, sections: [{time_estimate, text}]}.",
                "annotate": "Generate annotations for the recording. Return JSON: {annotations: [{timestamp, text, type}]}.",
                "schedule": "Schedule a recording session. Return JSON: {scheduled, start_time, duration, settings}.",
            },
            "default_prompt": "Assist with screen recording analysis and management.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "weather": {
            "action_prompts": {
                "outfit_suggest": "Based on the weather conditions, suggest appropriate clothing and accessories. Return JSON: {outfit: {top, bottom, outerwear, accessories: [], tip}}.",
                "travel_advice": "Provide travel advice based on current and forecast weather. Return JSON: {advice, precautions: [], best_time, transport_tips}.",
                "schedule_adjust": "Suggest schedule adjustments based on weather conditions. Return JSON: {adjustments: [{original_plan, suggested_change, reason}], indoor_alternatives: []}.",
                "health_tip": "Provide health tips based on weather conditions (UV, air quality, temperature). Return JSON: {tips: [{category, advice, priority}], warnings: []}.",
            },
            "default_prompt": "Assist with weather-related advice.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "mindmap": {
            "action_prompts": {
                "generate": "Generate a mind map structure from the given topic or content. Return JSON: {root: {text, children: [{text, children: [{text}]}]}}.",
                "expand_node": "Expand a specific mind map node with more sub-topics. Return JSON: {children: [{text, description}]}",
                "to_tasks": "Convert mind map nodes into actionable tasks. Return JSON: {tasks: [{title, description, priority, node_path}]}.",
                "summarize": "Summarize the mind map content into a concise overview. Return JSON: {summary, key_insights, recommendations}.",
            },
            "default_prompt": "Assist with mind map creation and analysis.",
            "category": "PLANNING",
            "default_return": {"result": ""},
        },
        "notes": {
            "action_prompts": {
                "summarize": "Summarize the note content concisely. Return JSON: {summary, key_points}.",
                "auto_tag": "Auto-tag the note with relevant tags. Return JSON: {tags: [{name, confidence}]}.",
                "link_suggest": "Suggest related notes to link. Return JSON: {suggestions: [{title, reason, relevance}]}.",
                "generate": "Generate a structured note from the given content or conversation. Return JSON: {title, content, tags: []}.",
                "refine": "Refine and improve the note content. Return JSON: {refined_content, changes: [{section, improvement}]}.",
                "polish": "Polish the note content for better readability and flow. Keep the original meaning. Return JSON: {polished_content}.",
                "correct": "Correct grammar, spelling, and punctuation errors in the note. Return JSON: {corrected_content, issues: [{original, corrected, type}]}.",
                "sprout": "Analyze the note deeply and generate a sprout report with structured sections. Each section should have a title, detailed content expanding on the original note, and an 'aha moment' insight. Return JSON: {title, sections: [{number, title, content, aha_moment}]}.",
                "extract_url": "Extract and parse content from the given URL. Generate a structured note with title, summary, key points, and tags. Return JSON: {title, structured_content, summary, key_points: [], tags: []}.",
                "ocr_note": "Recognize and extract text from the image description. Generate a structured note. Return JSON: {title, content, tags: []}.",
                "voice_correct": "Correct transcription errors from voice input. Fix punctuation, grammar, and unclear words. Return JSON: {corrected_content, changes: [{original, corrected}]}.",
                "outline": "Generate a structured outline for the note content. Return JSON: {outline: [{level, text}], title}.",
                "template": "Generate a note template based on the given topic or type. Return JSON: {title, content, tags: []}.",
                "organize": "Organize and restructure the note content logically. Return JSON: {organized_content, structure: [{section, items}]}.",
            },
            "default_prompt": "Assist with note-taking. Return JSON with the result.",
            "category": "MEMORY",
            "default_return": {"result": ""},
        },
        "contacts": {
            "action_prompts": {
                "enrich": "Enrich contact information with additional details. Return JSON: {suggested_fields: [{field, value, source}], confidence}.",
                "suggest_connect": "Suggest who to connect with based on context. Return JSON: {suggestions: [{name, reason, timing}]}.",
                "prepare_meeting": "Prepare meeting brief for contacts. Return JSON: {brief: {attendees: [{name, role, key_info}], topics, prep_items}}.",
                "remind_special": "Identify upcoming special dates for contacts. Return JSON: {reminders: [{contact, date, type, suggestion}]}.",
            },
            "default_prompt": "Assist with contact management.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "focus": {
            "action_prompts": {
                "recommend_duration": "Recommend focus session duration based on task. Return JSON: {duration_minutes, break_minutes, reason, technique}.",
                "session_summary": "Summarize the focus session productivity. Return JSON: {productivity_score, highlights, suggestions}.",
                "weekly_report": "Generate a weekly focus report. Return JSON: {total_hours, sessions, top_tasks, patterns, recommendations}.",
                "break_suggest": "Suggest a break activity. Return JSON: {activity, duration, benefits}.",
            },
            "default_prompt": "Assist with focus and time management.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "image": {
            "action_prompts": {
                "describe": "Describe the image content in detail. Return JSON: {description, objects, colors, mood, style}.",
                "suggest_edit": "Suggest image edits and enhancements. Return JSON: {edits: [{type, description, params}]}.",
                "generate_prompt": "Generate an image creation prompt. Return JSON: {prompt, negative_prompt, style, parameters}.",
                "analyze_composition": "Analyze the image composition. Return JSON: {composition, balance, focal_points, suggestions}.",
            },
            "default_prompt": "Assist with image editing and design.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "reader": {
            "action_prompts": {
                "summarize_article": "Summarize the article. Return JSON: {summary, key_points, reading_time, category}.",
                "extract_info": "Extract key information from the content. Return JSON: {entities, facts, quotes, data_points}.",
                "recommend": "Recommend related reading based on interests. Return JSON: {recommendations: [{title, reason, relevance}]}.",
                "digest": "Create a daily reading digest. Return JSON: {digest: [{title, summary, source, category}], trends}.",
            },
            "default_prompt": "Assist with reading and content curation.",
            "category": "MEMORY",
            "default_return": {"result": ""},
        },
        "code": {
            "action_prompts": {
                "explain": "Explain the code in plain language. Return JSON: {explanation, complexity, key_concepts}.",
                "refactor": "Suggest refactoring improvements. Return JSON: {refactored_code, changes: [{type, description}], benefits}.",
                "generate": "Generate code from natural language description. Return JSON: {code, language, dependencies, usage}.",
                "review": "Review the code for issues. Return JSON: {issues: [{line, severity, type, description, fix}], score}.",
                "debug": "Help debug the code issue. Return JSON: {diagnosis, root_cause, fix, prevention}.",
            },
            "default_prompt": "Assist with code editing and development.",
            "category": "PLANNING",
            "default_return": {"result": ""},
        },
        "dev": {
            "action_prompts": {
                "create_app": "Generate a complete application scaffold from the user's description. Return JSON: {files: [{path, content}], summary, dependencies, uses_polyspace_plugins, publish_targets}.",
                "add_feature": "Add a feature to the existing application. Return JSON: {files: [{path, content, action}], summary, dependencies}.",
                "add_plugin": "Integrate a PolySpace platform plugin (cross-device-sync, ai-capability, cloud-storage, notification, user-identity). Return JSON: {files: [{path, content, action}], plugin_id, summary, publish_restriction}.",
                "generate_backend": "Generate backend API endpoints for the application. Return JSON: {files: [{path, content}], api_routes: [{method, path, description}], summary}.",
                "generate_ui": "Generate UI components for the application. Return JSON: {files: [{path, content}], components: [{name, description}], summary}.",
                "deploy_check": "Check if the application is ready for deployment. Return JSON: {ready, issues: [{severity, description, fix}], uses_polyspace_plugins, available_targets}.",
                "explain_code": "Explain the application code in plain language for non-developers. Return JSON: {explanation, architecture, data_flow, key_components}.",
                "fix_error": "Fix an error in the application. Return JSON: {diagnosis, fix, files: [{path, content, action}], prevention}.",
            },
            "default_prompt": "Assist with application development for the PolySpace Dev App. Help non-technical users build and deploy applications.",
            "category": "PLANNING",
            "default_return": {"result": ""},
        },
        "design": {
            "action_prompts": {
                "generate": "Generate a design prototype based on the description. Return JSON: {html, css, summary, skill_used, design_system}.",
                "iterate": "Iterate on the existing design based on feedback. Return JSON: {html, css, changes: [{description}], summary}.",
                "change_style": "Change the visual style or design system. Return JSON: {html, css, style_changes, summary}.",
                "add_section": "Add a new section to the design. Return JSON: {html, css, section_added, summary}.",
                "remove_section": "Remove a section from the design. Return JSON: {html, css, section_removed, summary}.",
                "adjust_layout": "Adjust the layout of the design. Return JSON: {html, css, layout_changes, summary}.",
                "change_colors": "Change the color scheme. Return JSON: {html, css, color_changes, summary}.",
                "change_typography": "Change the typography. Return JSON: {html, css, typography_changes, summary}.",
                "export_ppt": "Convert the design to a format suitable for the PPT application. Return JSON: {slides: [{title, content, layout}], summary}.",
                "export_dev": "Convert the design to a format suitable for the Dev application, with AI-enhanced logic and backend. Return JSON: {files: [{path, content}], summary, ai_enhancements}.",
                "critique": "Provide a five-dimension design critique. Return JSON: {scores: {philosophy, hierarchy, execution, specificity, restraint}, issues, suggestions}.",
            },
            "default_prompt": "Assist with AI-driven design for the PolySpace Design App. Generate and iterate on visual designs.",
            "category": "PLANNING",
            "default_return": {"result": ""},
        },
        "finance": {
            "action_prompts": {
                "categorize": "Categorize the transaction. Return JSON: {category, subcategory, confidence}.",
                "budget_check": "Check budget status and provide alerts. Return JSON: {status, alerts: [{category, spent, budget, percentage}], recommendations}.",
                "report": "Generate a financial report. Return JSON: {summary, income, expenses: [{category, amount}], savings_rate, trends}.",
                "forecast": "Forecast future finances. Return JSON: {forecast: [{month, projected_income, projected_expenses}], confidence, assumptions}.",
            },
            "default_prompt": "Assist with financial management.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "calculator": {
            "action_prompts": {
                "compute": "Compute the mathematical expression. Return JSON: {result, steps: [{step, explanation}], formula_used}.",
                "convert": "Convert between units or currencies. Return JSON: {from_value, from_unit, to_value, to_unit, rate, explanation}.",
                "derive": "Derive or prove a mathematical formula. Return JSON: {formula, derivation: [{step}], result}.",
                "explain": "Explain a mathematical concept. Return JSON: {concept, explanation, examples: [{problem, solution}], applications}.",
            },
            "default_prompt": "Assist with calculations and mathematical reasoning.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "music": {
            "action_prompts": {
                "recommend": "Recommend music based on mood or activity. Return JSON: {tracks: [{title, artist, genre, reason}], playlist_name}.",
                "ambient_suggest": "Suggest ambient sounds for focus or relaxation. Return JSON: {sounds: [{name, type, duration, benefit}], mix_description}.",
                "mood_match": "Match music to the current mood or context. Return JSON: {mood_analysis, recommendations: [{title, artist, match_reason}]}.",
                "create_playlist": "Create a playlist for a specific purpose. Return JSON: {playlist: {name, purpose, tracks: [{title, artist}]}, total_duration}.",
            },
            "default_prompt": "Assist with music and ambient sound selection.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
        "ppt_summary": {
            "action_prompts": {
                "summarize_presentation": "Summarize the entire presentation. Return JSON: {summary, key_points, duration_estimate}.",
            },
            "default_prompt": "Summarize the presentation.",
            "category": "DAILY",
            "default_return": {"result": ""},
        },
    }

    def __init__(self, llm_dispatcher):
        self._dispatcher = llm_dispatcher

    def _resolve_category(self, task_type: str, action: Optional[str] = None):
        from app.core.llm.dispatcher import TaskCategory

        config = self._TASK_CONFIGS[task_type]
        category_name = config.get("category", "DAILY")
        overrides = config.get("category_overrides", {})
        if action and action in overrides:
            category_name = overrides[action]
        return getattr(TaskCategory, category_name)

    async def _execute_ai_task(
        self,
        task_category,
        messages: list,
        default_return: dict,
        fallback_key: Optional[str] = "result",
    ) -> dict:
        response = await self._dispatcher.dispatch(task_category, messages=messages)
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            if fallback_key:
                fallback = dict(default_return)
                fallback[fallback_key] = content
                return fallback
            return default_return

    async def _execute_action_task(
        self,
        task_type: str,
        action: str,
        user_content: str,
        default_return_kwargs: Optional[dict] = None,
    ) -> dict:
        config = self._TASK_CONFIGS[task_type]
        action_prompts = config.get("action_prompts", {})
        prompt = action_prompts.get(action, config.get("default_prompt", ""))
        suffix = config.get("suffix", "")
        category = self._resolve_category(task_type, action)
        messages = [
            {"role": "system", "content": prompt + suffix},
            {"role": "user", "content": user_content},
        ]
        default_return = config.get("default_return", {"result": ""})
        if default_return_kwargs:
            factory = config.get("default_return_factory")
            if factory:
                default_return = factory(**default_return_kwargs)
        return await self._execute_ai_task(category, messages, default_return)

    async def ai_video_analyze(self, video_info: dict) -> dict:
        config = self._TASK_CONFIGS["video_analyze"]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional video editing assistant. Analyze the video project "
                    "and provide intelligent suggestions. Return JSON: "
                    "{suggestions: [{type, description, confidence}], auto_edit_plan: {steps: [{action, params, reason}]}, "
                    "style_analysis: {mood, pace, genre_suggestion}}"
                ),
            },
            {"role": "user", "content": json.dumps(video_info, ensure_ascii=False)},
        ]
        category = self._resolve_category("video_analyze")
        return await self._execute_ai_task(category, messages, config["default_return"], fallback_key=None)

    async def ai_generate_subtitles(self, transcription: str, language: str = "zh") -> dict:
        config = self._TASK_CONFIGS["generate_subtitles"]
        messages = [
            {
                "role": "system",
                "content": (
                    "Generate formatted subtitles from transcription text. "
                    "Split into natural segments with timestamps. Return JSON: "
                    "{subtitles: [{start_time, end_time, text}], language, total_segments}"
                ),
            },
            {"role": "user", "content": f"Language: {language}\nTranscription:\n{transcription}"},
        ]
        category = self._resolve_category("generate_subtitles")
        default_return = config["default_return_factory"](language=language)
        return await self._execute_ai_task(category, messages, default_return, fallback_key=None)

    async def ai_document_assist(self, action: str, content: str, context: str = "", operation_path: str = "") -> dict:
        user_content = f"Content: {content}\nContext: {context}"
        if operation_path:
            user_content += f"\nUser operation path: {operation_path}"
        return await self._execute_action_task("document", action, user_content)

    async def ai_ppt_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("ppt", action, json.dumps(params, ensure_ascii=False))

    async def ai_excel_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("excel", action, json.dumps(params, ensure_ascii=False))

    async def ai_calendar_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("calendar", action, json.dumps(params, ensure_ascii=False))

    async def ai_knowledge_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("knowledge", action, json.dumps(params, ensure_ascii=False))

    async def ai_todo_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("todo", action, json.dumps(params, ensure_ascii=False))

    async def ai_email_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("email", action, json.dumps(params, ensure_ascii=False))

    async def ai_memo_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("memo", action, json.dumps(params, ensure_ascii=False))

    async def ai_kanban_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("kanban", action, json.dumps(params, ensure_ascii=False))

    async def ai_recorder_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("recorder", action, json.dumps(params, ensure_ascii=False))

    async def ai_weather_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("weather", action, json.dumps(params, ensure_ascii=False))

    async def ai_mindmap_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("mindmap", action, json.dumps(params, ensure_ascii=False))

    async def ai_notes_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("notes", action, json.dumps(params, ensure_ascii=False))

    async def ai_contacts_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("contacts", action, json.dumps(params, ensure_ascii=False))

    async def ai_focus_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("focus", action, json.dumps(params, ensure_ascii=False))

    async def ai_image_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("image", action, json.dumps(params, ensure_ascii=False))

    async def ai_reader_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("reader", action, json.dumps(params, ensure_ascii=False))

    async def ai_code_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("code", action, json.dumps(params, ensure_ascii=False))

    async def ai_dev_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("dev", action, json.dumps(params, ensure_ascii=False))

    async def ai_design_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("design", action, json.dumps(params, ensure_ascii=False))

    async def ai_finance_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("finance", action, json.dumps(params, ensure_ascii=False))

    async def ai_calculator_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("calculator", action, json.dumps(params, ensure_ascii=False))

    async def ai_music_assist(self, action: str, params: dict) -> dict:
        return await self._execute_action_task("music", action, json.dumps(params, ensure_ascii=False))

    async def ai_ppt_summary(self, slides: list[dict]) -> dict:
        return await self._execute_action_task(
            "ppt_summary", "summarize_presentation",
            json.dumps({"slides": slides}, ensure_ascii=False),
        )

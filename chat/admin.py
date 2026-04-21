# chat/admin.py
 
# ============================================================
# SEMICONCHAT — Admin Chat Interface
#
# Adds a custom page at /admin/chat/semiconchat/ that gives
# the admin a full chat interface wired to the same RAG
# pipeline used by the API:
#
#   Admin types query
#        ↓
#   POST to /admin/chat/semiconchat/
#        ↓
#   query_chatbot() called directly (same service as API)
#        ↓
#   LlamaIndex Query Engine
#        ↓
#   1. Embed query (HuggingFace bge-base, local)
#   2. Retrieve top-k from Pinecone
#   3. Apply filters if process/stage selected
#   4. Pass context + query to Groq LLM
#        ↓
#   LLM generates grounded answer
#        ↓
#   Answer + sources rendered in admin page
#   Session + messages saved to PostgreSQL automatically
#
# HOW IT WORKS IN DJANGO ADMIN:
#   - SemiconChat is a proxy model of ChatSession (no new DB table)
#   - get_urls() injects /admin/chat/semiconchat/ into the admin router
#   - semiconchat_view() handles GET (show form) and POST (run query)
#   - "SemiconChat" appears in the sidebar under "CHAT"
# ============================================================
 
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponse
from django.middleware.csrf import get_token
 
from .models import ChatSession, ChatMessage, Feedback, SemiconChat
from .services import query_chatbot
 
 
# ────────────────────────────────────────────────────────────
# Inline HTML template for the SemiconChat page
# ────────────────────────────────────────────────────────────
SEMICONCHAT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>SemiconChat | Admin</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f6fa; color: #263238; }}
 
    /* ── Wrapper ── */
    .sc-wrap {{ max-width: 900px; margin: 0 auto; padding: 28px 20px 60px; }}
 
    /* ── Header ── */
    .sc-header {{
      background: linear-gradient(135deg, #1a237e, #283593);
      color: white;
      padding: 22px 28px;
      border-radius: 10px;
      margin-bottom: 22px;
    }}
    .sc-header h1 {{ font-size: 21px; font-weight: 700; margin-bottom: 4px; }}
    .sc-header p  {{ font-size: 13px; opacity: 0.8; margin-bottom: 10px; }}
    .sc-chips {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .sc-chip {{
      background: rgba(255,255,255,0.18);
      border-radius: 12px;
      padding: 3px 11px;
      font-size: 11px;
      font-weight: 600;
    }}
 
    /* ── Pipeline banner ── */
    .sc-pipeline {{
      display: flex;
      align-items: center;
      gap: 6px;
      background: #e8eaf6;
      border: 1px solid #c5cae9;
      border-radius: 8px;
      padding: 11px 16px;
      margin-bottom: 22px;
      flex-wrap: wrap;
    }}
    .sc-step {{
      background: #1a237e;
      color: white;
      border-radius: 4px;
      padding: 3px 10px;
      font-size: 11px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .sc-arrow {{ color: #5c6bc0; font-size: 15px; font-weight: bold; }}
 
    /* ── Cards ── */
    .sc-card {{
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 10px;
      padding: 22px 24px;
      margin-bottom: 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }}
    .sc-card-title {{
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: #546e7a;
      margin-bottom: 14px;
    }}
 
    /* ── Textarea ── */
    textarea {{
      width: 100%;
      min-height: 88px;
      padding: 12px 14px;
      border: 1px solid #cfd8dc;
      border-radius: 7px;
      font-size: 14px;
      font-family: inherit;
      resize: vertical;
      transition: border 0.2s, box-shadow 0.2s;
      line-height: 1.5;
    }}
    textarea:focus {{
      outline: none;
      border-color: #3949ab;
      box-shadow: 0 0 0 3px rgba(57,73,171,0.12);
    }}
 
    /* ── Filters row ── */
    .sc-filters {{ display: flex; gap: 14px; margin-top: 14px; flex-wrap: wrap; }}
    .sc-filter {{
      display: flex;
      flex-direction: column;
      gap: 5px;
      flex: 1;
      min-width: 155px;
    }}
    .sc-filter label {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      color: #78909c;
    }}
    .sc-filter select {{
      padding: 8px 10px;
      border: 1px solid #cfd8dc;
      border-radius: 6px;
      font-size: 13px;
      background: white;
      cursor: pointer;
    }}
 
    /* ── Submit row ── */
    .sc-submit-row {{
      display: flex;
      align-items: center;
      gap: 16px;
      margin-top: 18px;
    }}
    .sc-btn {{
      background: #1a237e;
      color: white;
      border: none;
      padding: 10px 30px;
      border-radius: 7px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.18s, transform 0.1s;
    }}
    .sc-btn:hover  {{ background: #283593; }}
    .sc-btn:active {{ transform: scale(0.98); }}
    #sc-loading {{
      display: none;
      font-size: 13px;
      color: #7986cb;
      font-style: italic;
    }}
    .sc-hint {{ font-size: 12px; color: #b0bec5; }}
 
    /* ── Answer ── */
    .sc-answer {{
      font-size: 14px;
      line-height: 1.75;
      color: #263238;
      white-space: pre-wrap;
      border-left: 4px solid #1a237e;
      padding-left: 16px;
      margin-top: 4px;
    }}
    .sc-meta {{
      margin-top: 12px;
      font-size: 12px;
      color: #90a4ae;
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
    }}
    .sc-meta span {{ background: #f5f5f5; padding: 2px 8px; border-radius: 4px; }}
 
    /* ── Sources ── */
    .sc-source {{
      border: 1px solid #eceff1;
      border-radius: 7px;
      padding: 14px 16px;
      margin-bottom: 10px;
      background: #fafafa;
    }}
    .sc-source:last-child {{ margin-bottom: 0; }}
    .sc-source-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .sc-source-title {{ font-weight: 700; font-size: 13px; color: #37474f; }}
    .sc-badges {{ display: flex; gap: 5px; flex-wrap: wrap; }}
    .badge {{
      border-radius: 10px;
      padding: 2px 9px;
      font-size: 11px;
      font-weight: 700;
    }}
    .badge-process {{ background: #e8eaf6; color: #3949ab; }}
    .badge-stage   {{ background: #fce4ec; color: #c2185b; }}
    .badge-type    {{ background: #e0f2f1; color: #00695c; }}
    .badge-score   {{ background: #e8f5e9; color: #2e7d32; }}
    .sc-source-text {{
      font-size: 12px;
      color: #607d8b;
      line-height: 1.65;
      font-style: italic;
    }}
 
    /* ── Error ── */
    .sc-error {{
      background: #ffebee;
      border: 1px solid #ef9a9a;
      border-radius: 8px;
      padding: 14px 18px;
      color: #b71c1c;
      font-size: 14px;
      margin-bottom: 18px;
    }}
    .sc-error small {{ display: block; margin-top: 5px; color: #e57373; font-size: 12px; }}
 
    /* ── No sources ── */
    .sc-no-sources {{ font-size: 13px; color: #90a4ae; font-style: italic; }}
  </style>
</head>
<body>
<div class="sc-wrap">
 
  <!-- Header -->
  <div class="sc-header">
    <h1>⚙️ SemiconChat</h1>
    <p>RAG-powered semiconductor manufacturing expert — Admin Interface</p>
    <div class="sc-chips">
      <span class="sc-chip">Groq LLM</span>
      <span class="sc-chip">Pinecone Vector DB</span>
      <span class="sc-chip">LlamaIndex RAG</span>
      <span class="sc-chip">HuggingFace Embeddings</span>
    </div>
  </div>
 
  <!-- Pipeline steps -->
  <div class="sc-pipeline">
    <span class="sc-step">1. Embed Query</span>
    <span class="sc-arrow">→</span>
    <span class="sc-step">2. Retrieve top-k (Pinecone)</span>
    <span class="sc-arrow">→</span>
    <span class="sc-step">3. Metadata Filters</span>
    <span class="sc-arrow">→</span>
    <span class="sc-step">4. Groq LLM</span>
    <span class="sc-arrow">→</span>
    <span class="sc-step">5. Answer + Sources</span>
  </div>
 
  <!-- Error -->
  {error_html}
 
  <!-- Answer -->
  {answer_html}
 
  <!-- Sources -->
  {sources_html}
 
  <!-- Query form -->
  <div class="sc-card">
    <div class="sc-card-title">Ask a Question</div>
    <form method="post">
      <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
 
      <textarea
        id="query"
        name="query"
        placeholder="e.g. What are the critical parameters for plasma etch rate control in FEOL dry etching?"
      >{previous_query}</textarea>
 
      <div class="sc-filters">
        <div class="sc-filter">
          <label>Filter by Process</label>
          <select name="process">
            <option value="">All Processes</option>
            <option value="lithography"   {sel_lithography}>Lithography</option>
            <option value="etching"       {sel_etching}>Etching</option>
            <option value="deposition"    {sel_deposition}>Deposition</option>
            <option value="cmp"           {sel_cmp}>CMP</option>
            <option value="implantation"  {sel_implantation}>Ion Implantation</option>
            <option value="diffusion"     {sel_diffusion}>Diffusion</option>
            <option value="metallization" {sel_metallization}>Metallization</option>
            <option value="inspection"    {sel_inspection}>Inspection &amp; Metrology</option>
            <option value="general"       {sel_proc_general}>General</option>
          </select>
        </div>
        <div class="sc-filter">
          <label>Filter by Fab Stage</label>
          <select name="stage">
            <option value="">All Stages</option>
            <option value="FEOL"    {sel_feol}>FEOL (Front End of Line)</option>
            <option value="BEOL"    {sel_beol}>BEOL (Back End of Line)</option>
            <option value="general" {sel_stage_general}>General</option>
          </select>
        </div>
      </div>
 
      <div class="sc-submit-row">
        <button class="sc-btn" type="submit" onclick="showLoading()">
          Ask SemiconChat
        </button>
        <span id="sc-loading">⏳ Querying Pinecone and Groq LLM…</span>
        <span class="sc-hint">Session saved to chat history automatically</span>
      </div>
    </form>
  </div>
 
</div>
<script>
  function showLoading() {{
    document.getElementById('sc-loading').style.display = 'inline';
  }}
  document.addEventListener('DOMContentLoaded', function() {{
    var ta = document.getElementById('query');
    if (ta) {{ ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); }}
  }});
</script>
</body>
</html>
"""

@admin.register(SemiconChat)
class SemiconChatAdmin(admin.ModelAdmin):
 
    def get_urls(self):
        """
        Override get_urls() to inject the custom chat page URL.
        We return ONLY our custom URL — no changelist/add/change
        URLs since this isn't a normal model admin.
 
        Django admin resolves /admin/chat/semiconchat/ to
        semiconchat_view() via this registration.
        """
        return [
            path(
                '',
                self.admin_site.admin_view(self.semiconchat_view),
                name='chat_semiconchat_changelist',
                # name must follow pattern: <app>_<model>_changelist
                # so the sidebar "SemiconChat" link works automatically
            ),
        ]
 
    def semiconchat_view(self, request):
        """
        GET  → render empty form
        POST → run full RAG pipeline, render answer + sources
 
        The complete query flow on POST:
          query_chatbot(user, query, filters)
            └─ build_query_engine(process_filter, stage_filter)
                 ├─ VectorIndexRetriever  →  Pinecone top-5 chunks
                 └─ RetrieverQueryEngine  →  Groq LLM synthesis
            └─ Save ChatSession + ChatMessage to PostgreSQL
            └─ Return { answer, sources, session_id, message_id }
        """
        answer_html  = ''
        sources_html = ''
        error_html   = ''
        previous_query = ''
 
        # Track which dropdown options were selected (persist after submit)
        sel = {k: '' for k in [
            'lithography', 'etching', 'deposition', 'cmp',
            'implantation', 'diffusion', 'metallization',
            'inspection', 'proc_general',
            'feol', 'beol', 'stage_general',
        ]}
 
        if request.method == 'POST':
            user_query     = request.POST.get('query', '').strip()
            process_filter = request.POST.get('process') or None
            stage_filter   = request.POST.get('stage')   or None
            previous_query = user_query
 
            # Restore dropdown state
            if process_filter:
                key = process_filter if process_filter != 'general' else 'proc_general'
                if key in sel:
                    sel[key] = 'selected'
            if stage_filter == 'FEOL':
                sel['feol'] = 'selected'
            elif stage_filter == 'BEOL':
                sel['beol'] = 'selected'
            elif stage_filter == 'general':
                sel['stage_general'] = 'selected'
 
            if not user_query:
                error_html = '<div class="sc-error">⚠️ Please enter a question before submitting.</div>'
 
            else:
                try:
                    # ── Run the full RAG pipeline ──
                    result = query_chatbot(
                        user=request.user,
                        user_query=user_query,
                        session_id=None,
                        process_filter=process_filter,
                        stage_filter=stage_filter,
                    )
 
                    if 'error' in result:
                        error_html = f'<div class="sc-error">⚠️ {result["error"]}</div>'
 
                    else:
                        # ── Answer block ──
                        filter_meta = ''
                        if process_filter:
                            filter_meta += f'<span>Process: {process_filter}</span>'
                        if stage_filter:
                            filter_meta += f'<span>Stage: {stage_filter}</span>'
 
                        answer_html = f"""
                        <div class="sc-card">
                          <div class="sc-card-title">💬 Answer</div>
                          <div class="sc-answer">{result['answer']}</div>
                          <div class="sc-meta">
                            <span>Session #{result['session_id']}</span>
                            <span>Message #{result['message_id']}</span>
                            <span>{len(result['sources'])} sources retrieved</span>
                            {filter_meta}
                          </div>
                        </div>
                        """
 
                        # ── Sources block ──
                        if result['sources']:
                            items = ''
                            for i, src in enumerate(result['sources'], 1):
                                p_badge  = f'<span class="badge badge-process">{src["process"]}</span>'   if src.get('process')  else ''
                                s_badge  = f'<span class="badge badge-stage">{src["stage"]}</span>'       if src.get('stage')    else ''
                                dt_badge = f'<span class="badge badge-type">{src["doc_type"]}</span>'     if src.get('doc_type') else ''
                                sc_badge = f'<span class="badge badge-score">score {src["score"]}</span>' if src.get('score')    else ''
                                items += f"""
                                <div class="sc-source">
                                  <div class="sc-source-head">
                                    <span class="sc-source-title">[{i}] {src.get('doc_title','Unknown Document')}</span>
                                    <div class="sc-badges">{p_badge}{s_badge}{dt_badge}{sc_badge}</div>
                                  </div>
                                  <div class="sc-source-text">"{src.get('text','')}"</div>
                                </div>
                                """
                            sources_html = f"""
                            <div class="sc-card">
                              <div class="sc-card-title">📄 Retrieved Sources — {len(result['sources'])} chunks from Pinecone</div>
                              {items}
                            </div>
                            """
                        else:
                            sources_html = """
                            <div class="sc-card">
                              <div class="sc-card-title">📄 Retrieved Sources</div>
                              <p class="sc-no-sources">
                                No matching chunks found in Pinecone for this query.
                                Make sure documents have been uploaded and indexed first.
                              </p>
                            </div>
                            """
 
                except Exception as e:
                    error_html = f"""
                    <div class="sc-error">
                      ❌ Pipeline error: {str(e)}
                      <small>Check that Pinecone is reachable and at least one document has been indexed via the Documents admin.</small>
                    </div>
                    """
 
        html = SEMICONCHAT_HTML.format(
            csrf_token      = get_token(request),
            error_html      = error_html,
            answer_html     = answer_html,
            sources_html    = sources_html,
            previous_query  = previous_query,
            sel_lithography   = sel['lithography'],
            sel_etching       = sel['etching'],
            sel_deposition    = sel['deposition'],
            sel_cmp           = sel['cmp'],
            sel_implantation  = sel['implantation'],
            sel_diffusion     = sel['diffusion'],
            sel_metallization = sel['metallization'],
            sel_inspection    = sel['inspection'],
            sel_proc_general  = sel['proc_general'],
            sel_feol          = sel['feol'],
            sel_beol          = sel['beol'],
            sel_stage_general = sel['stage_general'],
        )
        return HttpResponse(html)
 
    # Hide all default model admin buttons
    def has_add_permission(self, request):             return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'content', 'sources', 'created_at')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'created_at', 'message_count')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    inlines = [ChatMessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'short_content', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content',)

    def short_content(self, obj):
        return obj.content[:80]
    short_content.short_description = 'Content'

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'vote', 'created_at')
    list_filter = ('vote',)


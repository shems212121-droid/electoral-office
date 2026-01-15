from django.urls import path
from django.contrib.auth.views import LogoutView
from django.views.generic import RedirectView
from . import views
from . import reports
from . import vote_count_views
from . import comprehensive_reports
from . import public_views
from . import user_management_views
from . import dashboard_views
from . import barcode_views
from . import views_calculator
from . import center_views
from . import director_views
from . import admin_views
from . import result_entry_views
from . import task_notifications
from . import communication_views
from . import sub_room_views



urlpatterns = [
    # Authentication
    path('', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # PWA Offline Page
    path('offline/', views.offline_page, name='offline'),
    
    # Voters
    path('reset-data/', views.DataResetView.as_view(), name='data_reset'),
    path('voters/', views.VoterListView.as_view(), name='voter_list'),
    path('voters/<int:pk>/', views.VoterDetailView.as_view(), name='voter_detail'),
    path('voter-search/', views.VoterSearchView.as_view(), name='voter_search'),
    path('voters/<int:voter_pk>/log/', views.log_communication, name='log_communication'),
    path('api/voter-lookup/', views.voter_lookup_ajax, name='voter_lookup_ajax'),
    
    # Candidates - Unified (using PartyCandidate as the single source)
    path('candidates/', views.PartyCandidateListView.as_view(), name='candidate_list'),
    path('candidates/create/', views.PartyCandidateCreateView.as_view(), name='candidate_create'),
    path('candidates/<int:pk>/', views.PartyCandidateDetailView.as_view(), name='candidate_detail'),
    path('candidates/<int:pk>/edit/', views.PartyCandidateUpdateView.as_view(), name='candidate_edit'),
    path('candidates/<int:pk>/delete/', views.PartyCandidateDeleteView.as_view(), name='candidate_delete'),
    
    # Anchors
    path('anchors/', views.AnchorListView.as_view(), name='anchor_list'),
    path('anchors/create/', views.AnchorCreateView.as_view(), name='anchor_create'),
    path('anchors/<int:pk>/', views.AnchorDetailView.as_view(), name='anchor_detail'),
    path('anchors/<int:pk>/edit/', views.AnchorUpdateView.as_view(), name='anchor_edit'),
    path('anchors/<int:pk>/delete/', views.AnchorDeleteView.as_view(), name='anchor_delete'),
    
    # Introducers
    path('introducers/', views.IntroducerListView.as_view(), name='introducer_list'),
    path('introducers/create/', views.IntroducerCreateView.as_view(), name='introducer_create'),
    path('introducers/<int:pk>/', views.IntroducerDetailView.as_view(), name='introducer_detail'),
    path('introducers/<int:pk>/edit/', views.IntroducerUpdateView.as_view(), name='introducer_edit'),
    path('introducers/<int:pk>/delete/', views.IntroducerDeleteView.as_view(), name='introducer_delete'),
    path('introducers/<int:pk>/voters/', views.IntroducerVotersView.as_view(), name='introducer_voters'),
    path('introducers/<int:pk>/voters/add/', views.add_voter_to_introducer, name='add_voter_to_introducer'),
    path('introducers/<int:pk>/voters/remove/', views.remove_voter_from_introducer, name='remove_voter_from_introducer'),
    path('introducers/<int:pk>/voters/bulk-add/', views.bulk_add_voters_to_introducer, name='bulk_add_voters_to_introducer'),
    
    # Tasks
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/status/', views.task_change_status, name='task_change_status'),
    # API for overdue tasks
    path('api/tasks/overdue/', task_notifications.get_overdue_tasks, name='api_overdue_tasks'),
    
    path('monitors/', views.MonitorListView.as_view(), name='monitor_list'),
    path('monitors/create/', views.MonitorCreateView.as_view(), name='monitor_create'),
    path('monitors/<int:pk>/', views.MonitorDetailView.as_view(), name='monitor_detail'),
    path('monitors/<int:pk>/edit/', views.MonitorUpdateView.as_view(), name='monitor_edit'),
    path('monitors/<int:pk>/delete/', views.MonitorDeleteView.as_view(), name='monitor_delete'),
    
    # Center Directors (مدراء المراكز الانتخابية)
    path('center-directors/', center_views.center_director_list, name='center_director_list'),
    path('center-directors/add/', center_views.center_director_add, name='center_director_add'),
    path('center-directors/<int:pk>/', center_views.center_director_detail, name='center_director_detail'),
    path('center-directors/<int:pk>/edit/', center_views.center_director_edit, name='center_director_edit'),
    path('center-directors/<int:pk>/delete/', center_views.center_director_delete, name='center_director_delete'),
    
    # Political Entity Agents (وكلاء الكيان)
    path('political-entity-agents/', center_views.political_entity_agent_list, name='political_entity_agent_list'),
    path('political-entity-agents/add/', center_views.political_entity_agent_add, name='political_entity_agent_add'),
    path('political-entity-agents/<int:pk>/', center_views.political_entity_agent_detail, name='political_entity_agent_detail'),
    path('political-entity-agents/<int:pk>/edit/', center_views.political_entity_agent_edit, name='political_entity_agent_edit'),
    path('political-entity-agents/<int:pk>/delete/', center_views.political_entity_agent_delete, name='political_entity_agent_delete'),
    
    # API/AJAX for Centers
    path('api/agents-by-center/', center_views.get_agents_by_center, name='api_agents_by_center'),
    path('api/center-director-by-center/', center_views.get_center_director_by_center, name='api_center_director_by_center'),

    # ==================== Sub-Operation Rooms (غرف العمليات الفرعية) ====================
    # Force Reload: Updated URLs
    # Room Management
    path('sub-rooms/', sub_room_views.sub_room_list, name='sub_room_list'),
    path('sub-rooms/create/', sub_room_views.sub_room_create, name='sub_room_create'),
    path('sub-rooms/<int:pk>/update/', sub_room_views.sub_room_update, name='sub_room_update'),
    path('sub-rooms/<int:pk>/delete/', sub_room_views.sub_room_delete, name='sub_room_delete'),
    path('sub-rooms/<int:pk>/toggle-status/', sub_room_views.sub_room_toggle_status, name='sub_room_toggle_status'),
    
    # Room Dashboard and Details
    path('sub-rooms/<int:pk>/dashboard/', sub_room_views.sub_room_dashboard, name='sub_room_dashboard'),
    path('sub-rooms/<int:pk>/introducers/', sub_room_views.sub_room_introducers, name='sub_room_introducers'),
    path('sub-rooms/<int:pk>/voters/', sub_room_views.sub_room_voters, name='sub_room_voters'),
    path('sub-rooms/<int:pk>/directors/', sub_room_views.sub_room_directors, name='sub_room_directors'),
    path('sub-rooms/<int:pk>/agents/', sub_room_views.sub_room_agents, name='sub_room_agents'),
    
    # Statistics and Reports
    path('sub-rooms/statistics/', sub_room_views.sub_room_statistics, name='sub_room_statistics'),
    path('sub-rooms/comparison/', sub_room_views.sub_room_comparison, name='sub_room_comparison'),
    path('sub-rooms/<int:pk>/export/', sub_room_views.sub_room_export, name='sub_room_export'),

    
    # Comprehensive Reports (التقارير الشاملة)
    path('reports/comprehensive/', comprehensive_reports.comprehensive_reports_dashboard, name='comprehensive_reports'),
    path('reports/candidates/comprehensive/excel/', comprehensive_reports.export_candidates_comprehensive_excel, name='export_candidates_comprehensive_excel'),
    path('reports/candidates/comprehensive/csv/', comprehensive_reports.export_candidates_comprehensive_csv, name='export_candidates_comprehensive_csv'),
    path('reports/candidates/comprehensive/pdf/', comprehensive_reports.export_candidates_comprehensive_pdf, name='export_candidates_comprehensive_pdf'),
    path('reports/voters/comprehensive/excel/', comprehensive_reports.export_voters_comprehensive_excel, name='export_voters_comprehensive_excel'),
    path('reports/voters/comprehensive/csv/', comprehensive_reports.export_voters_comprehensive_csv, name='export_voters_comprehensive_csv'),
    path('reports/introducers/excel/', comprehensive_reports.export_introducers_excel, name='export_introducers_excel'),
    path('reports/introducers/csv/', comprehensive_reports.export_introducers_csv, name='export_introducers_csv'),
    path('reports/anchors/excel/', comprehensive_reports.export_anchors_excel, name='export_anchors_excel'),
    path('reports/anchors/csv/', comprehensive_reports.export_anchors_csv, name='export_anchors_csv'),
    path('reports/votes/excel/', comprehensive_reports.export_votes_excel, name='export_votes_excel'),
    path('reports/votes/csv/', comprehensive_reports.export_votes_csv, name='export_votes_csv'),
    path('reports/results/summary/excel/', comprehensive_reports.export_results_summary_excel, name='export_results_summary_excel'),
    
    # New Comprehensive Reports
    path('reports/center-directors/excel/', comprehensive_reports.export_center_directors_excel, name='export_center_directors_excel'),
    path('reports/center-directors/csv/', comprehensive_reports.export_center_directors_csv, name='export_center_directors_csv'),
    path('reports/monitors/excel/', comprehensive_reports.export_monitors_excel, name='export_monitors_excel'),
    path('reports/monitors/csv/', comprehensive_reports.export_monitors_csv, name='export_monitors_csv'),
    path('reports/agents/excel/', comprehensive_reports.export_agents_excel, name='export_agents_excel'),
    path('reports/agents/csv/', comprehensive_reports.export_agents_csv, name='export_agents_csv'),
    path('reports/archive/excel/', comprehensive_reports.export_archive_excel, name='export_archive_excel'),
    path('reports/archive/csv/', comprehensive_reports.export_archive_csv, name='export_archive_csv'),
    
    # Old Reports
    path('reports/', reports.reports_dashboard, name='reports_dashboard'),
    path('reports/voters/csv/', reports.export_voters_csv, name='export_voters_csv'),
    path('reports/voters/excel/', reports.export_voters_excel, name='export_voters_excel'),
    path('reports/candidates/csv/', reports.export_candidates_csv, name='export_candidates_csv'),
    path('reports/daily/', reports.daily_report_html, name='daily_report_html'),
    path('reports/daily/excel/', reports.export_daily_report_excel, name='export_daily_report_excel'),
    
    # Vote Counting System
    path('vote/parties/', views.PartyListView.as_view(), name='party_list'),
    path('vote/parties/create/', views.PartyCreateView.as_view(), name='party_create'),
    # Vote/Candidates - Redirect to unified candidate URLs
    path('vote/candidates/', RedirectView.as_view(pattern_name='candidate_list', permanent=True)),
    path('vote/candidates/create/', RedirectView.as_view(pattern_name='candidate_create', permanent=True)),
    path('vote/candidates/<int:pk>/', RedirectView.as_view(pattern_name='candidate_detail', permanent=True)),
    path('vote/candidates/<int:pk>/edit/', RedirectView.as_view(pattern_name='candidate_edit', permanent=True)),
    path('vote/candidates/<int:pk>/delete/', RedirectView.as_view(pattern_name='candidate_delete', permanent=True)),
    
    # Candidate Enhancements
    path('api/candidates/search/', views.party_candidate_search_ajax, name='party_candidate_search_ajax'),
    path('vote/candidates/export/excel/', reports.export_party_candidates_excel, name='export_party_candidates_excel'),
    path('vote/candidates/export/pdf/', reports.export_party_candidates_pdf, name='export_party_candidates_pdf'),
    path('vote/candidates/dashboard/', views.CandidateDashboardView.as_view(), name='candidates_dashboard'),
    
    path('vote/centers/', views.PollingCenterListView.as_view(), name='polling_center_list'),
    path('vote/centers/create/', views.PollingCenterCreateView.as_view(), name='polling_center_create'),
    path('vote/count/', views.QuickVoteCountView.as_view(), name='quick_vote_count'),
    path('vote/results/', views.ResultsDashboardView.as_view(), name='results_dashboard'),
    
    # New Vote Counting Routes (General & Special)
    path('vote/count/general/', vote_count_views.GeneralVoteCountView.as_view(), name='general_vote_count'),
    path('vote/count/special/', vote_count_views.SpecialVoteCountView.as_view(), name='special_vote_count'),
    path('vote/results/combined/', vote_count_views.CombinedResultsView.as_view(), name='combined_results'),
    
    # Vote Totals Dashboard
    path('vote/totals/', vote_count_views.VoteTotalsDashboardView.as_view(), name='vote_totals_dashboard'),
    
    
    # Tools / Calculator
    path('tools/sainte-lague/', views_calculator.SainteLagueCalculatorView.as_view(), name='sainte_lague_calculator'),

    # AJAX APIs for Vote Counting
    path('api/polling-center/<str:center_number>/', vote_count_views.get_polling_center_info, name='get_polling_center_info'),
    path('api/vote-totals/', vote_count_views.get_vote_totals_api, name='vote_totals_api'),
    path('api/vote-count/bulk-save/', vote_count_views.save_bulk_votes, name='save_bulk_votes'),
    
    # ==================== Electoral Public (المرتكزات) ====================
    path('electoral-public/', public_views.ElectoralPublicListView.as_view(), name='electoral_public_list'),
    path('electoral-public/create/', public_views.ElectoralPublicCreateView.as_view(), name='electoral_public_create'),
    path('electoral-public/<int:pk>/', public_views.ElectoralPublicDetailView.as_view(), name='electoral_public_detail'),
    path('electoral-public/<int:pk>/edit/', public_views.ElectoralPublicUpdateView.as_view(), name='electoral_public_update'),
    path('electoral-public/<int:pk>/delete/', public_views.ElectoralPublicDeleteView.as_view(), name='electoral_public_delete'),
    path('electoral-public/<int:pk>/approve/', public_views.approve_electoral_public, name='approve_electoral_public'),
    path('electoral-public/<int:pk>/reject/', public_views.reject_electoral_public, name='reject_electoral_public'),
    
    # ==================== Personal Voter Record (المعرفين) ====================
    path('my-voters/', public_views.PersonalVoterRecordView.as_view(), name='personal_voter_record'),
    path('my-voters/add/', public_views.add_voter_to_personal_record, name='add_voter_to_personal_record'),
    path('my-voters/<int:pk>/delete/', public_views.delete_personal_voter_record, name='delete_personal_voter_record'),
    path('my-voters/<int:pk>/classify/', public_views.update_voter_classification, name='update_voter_classification'),
    
    # ==================== Observer Registration (تسجيل المراقبين الجديد) ====================
    path('observer-registration/', public_views.ObserverRegistrationListView.as_view(), name='observer_registration_list'),
    path('observer-registration/create/', public_views.ObserverRegistrationCreateView.as_view(), name='observer_registration_create'),
    path('observer-registration/<int:pk>/', public_views.ObserverRegistrationDetailView.as_view(), name='observer_registration_detail'),
    path('observer-registration/<int:pk>/approve/', public_views.approve_observer, name='approve_observer'),
    path('observer-registration/<int:pk>/reject/', public_views.reject_observer, name='reject_observer'),
    path('observer-registration/<int:pk>/face-capture/', public_views.save_face_capture, name='save_face_capture'),
    
    # ==================== User Management (Admin Only) ====================
    path('users/', user_management_views.user_management_list, name='user_management_list'),
    path('users/create/', user_management_views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', user_management_views.user_edit, name='user_edit'),
    path('users/<int:user_id>/toggle/', user_management_views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:user_id>/delete/', user_management_views.user_delete, name='user_delete'),
    
    # Credential Generation
    path('users/generate-credentials/', user_management_views.generate_credentials_view, name='generate_credentials_view'),
    path('users/generate-credentials/candidate/', user_management_views.generate_credentials_candidate, name='generate_credentials_candidate'),
    path('users/generate-credentials/admin/', user_management_views.generate_credentials_admin, name='generate_credentials_admin'),
    path('users/generate-credentials/support/', user_management_views.generate_credentials_support, name='generate_credentials_support'),
    path('users/generate-credentials/room/', user_management_views.generate_credentials_room, name='generate_credentials_room'),
    
    # ==================== Role-Based Dashboards ====================
    path('dashboard/admin/', dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/supervisor/', dashboard_views.supervisor_dashboard, name='supervisor_dashboard'),
    path('dashboard/data-entry/', dashboard_views.data_entry_dashboard, name='data_entry_dashboard'),
    path('dashboard/viewer/', dashboard_views.viewer_dashboard, name='viewer_dashboard'),
    
    # New Role Dashboards
    path('dashboard/candidate/', dashboard_views.candidate_dashboard, name='candidates_dashboard'),
    path('dashboard/tech-support/', dashboard_views.tech_support_dashboard, name='tech_support_dashboard'),
    path('dashboard/ops-room/', dashboard_views.operations_room_dashboard, name='operations_room_dashboard'),
    
    # ==================== Barcode Scanner (IHEC Style) ====================
    # Main Scanner Interface
    path('barcode/scanner/', barcode_views.barcode_scanner, name='barcode_scanner'),
    
    # Session Management APIs
    path('barcode/api/session/start/', barcode_views.start_scan_session, name='start_scan_session'),
    path('barcode/api/session/<int:session_id>/end/', barcode_views.end_scan_session, name='end_scan_session'),
    
    # Barcode Processing API
    path('barcode/api/process/', barcode_views.process_barcode_scan, name='process_barcode_scan'),
    path('barcode/api/scan/<int:scan_id>/approve/', barcode_views.approve_and_process_scan, name='approve_and_process_scan'),
    
    # Session Lists and Details
    path('barcode/sessions/', barcode_views.scan_sessions_list, name='scan_sessions_list'),
    path('barcode/sessions/<int:pk>/', barcode_views.scan_session_detail, name='scan_session_detail'),
    
    # Reports
    path('barcode/reports/vote-count/', barcode_views.vote_count_report, name='barcode_vote_count_report'),
    
    # ==================== Director Dashboard (واجهة مدير المركز) ====================
    path('director/dashboard/', director_views.director_dashboard, name='director_dashboard'),
    path('director/agents/', director_views.director_agents_list, name='director_agents_list'),
    path('director/monitors/', director_views.director_monitors_list, name='director_monitors_list'),
    path('director/attendance/<str:person_type>/<int:person_id>/<str:action>/', 
         director_views.record_attendance, name='record_attendance'),
    path('director/attendance/history/', director_views.attendance_history, name='attendance_history'),
    path('director/logout/', director_views.director_logout, name='director_logout'),
    
    # ==================== Admin: Directors Monitoring (مراقبة المدراء للأدمن) ====================
    path('management/directors/monitor/', admin_views.admin_directors_monitor, name='admin_directors_monitor'),
    path('management/attendance/reports/', admin_views.attendance_reports, name='attendance_reports'),
    path('management/attendance/export-excel/', admin_views.export_attendance_excel, name='export_attendance_excel'),
    path('management/directors/<int:director_id>/activity/', admin_views.director_activity_detail, name='director_activity_detail'),
    
    # ==================== Result Entry (إدخال نتائج الانتخابات) ====================
    path('results/entry/dashboard/', result_entry_views.result_entry_dashboard, name='data_entry_results_dashboard'),
    path('results/entry/add/', result_entry_views.result_entry_add, name='result_entry_add'),
    
    # ==================== Unified Communications Hub ====================
    path('communications/', communication_views.communications_dashboard, name='communications_dashboard'),
    path('communications/search/', communication_views.search_contacts, name='search_contacts'),
    path('communications/log/', communication_views.log_call, name='log_call'),

    # ==================== Background Sync APIs ====================
    path('api/candidates/', views.api_candidates_list, name='api_candidates_list'),
    path('api/parties/', views.api_parties_list, name='api_parties_list'),
    
    # ==================== Emergency Tools ====================
    path('tool/import-voters-secret/', views.run_import_script, name='run_import_script'),
    path('tool/import-log/', views.view_import_log, name='view_import_log'),
    path('tool/link-hierarchy/', views.run_link_hierarchy, name='run_link_hierarchy'),
    path('tool/import-centers/', views.run_import_centers, name='run_import_centers'),
    path('tool/import-part2/', views.run_import_part2, name='run_import_part2'),
    path('tool/import-part3/', views.run_import_part3, name='run_import_part3'),
]


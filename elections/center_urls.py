from django.urls import path
from . import center_views

urlpatterns = [
    # Center Directors URLs
    path('center-directors/', center_views.center_director_list, name='center_director_list'),
    path('center-directors/add/', center_views.center_director_add, name='center_director_add'),
    path('center-directors/<int:pk>/', center_views.center_director_detail, name='center_director_detail'),
    path('center-directors/<int:pk>/edit/', center_views.center_director_edit, name='center_director_edit'),
    path('center-directors/<int:pk>/delete/', center_views.center_director_delete, name='center_director_delete'),
    
    # Political Entity Agents URLs
    path('political-entity-agents/', center_views.political_entity_agent_list, name='political_entity_agent_list'),
    path('political-entity-agents/add/', center_views.political_entity_agent_add, name='political_entity_agent_add'),
    path('political-entity-agents/<int:pk>/', center_views.political_entity_agent_detail, name='political_entity_agent_detail'),
    path('political-entity-agents/<int:pk>/edit/', center_views.political_entity_agent_edit, name='political_entity_agent_edit'),
    path('political-entity-agents/<int:pk>/delete/', center_views.political_entity_agent_delete, name='political_entity_agent_delete'),
    
    # API/AJAX URLs
    path('api/agents-by-center/', center_views.get_agents_by_center, name='api_agents_by_center'),
    path('api/center-director-by-center/', center_views.get_center_director_by_center, name='api_center_director_by_center'),
]

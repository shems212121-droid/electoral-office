from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class SainteLagueCalculatorView(LoginRequiredMixin, TemplateView):
    template_name = 'elections/sainte_lague_calculator.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # We can add default settings here if needed, but JS will handle most.
        # Default divisor for Iraq 2025 (Modified Sainte-Laguë) is usually 1.7
        context['default_divisor'] = 1.7 
        return context

from django.contrib import admin
from django.core.paginator import Paginator
from django.core.mail import mail_admins
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

from .models import ErrorLog, ErrorReport


def report_error(request, error_id):
    """
    View for users to report and provide additional context about an error
    """
    error_log = get_object_or_404(ErrorLog, id=error_id)
    
    if request.method == 'POST':
        user_description = request.POST.get('user_description', '')
        contact_info = request.POST.get('contact_info', '')
        
        # Create error report
        ErrorReport.objects.create(
            error_log=error_log,
            user_description=user_description,
            contact_info=contact_info
        )
        
        # Send notification to admins
        subject = f'[OKGBI] Пользовательский отчет об ошибке #{error_id}'
        message = f"""
        Пользователь оставил отчет об ошибке #{error_id}:
        
        Описание пользователя:
        {user_description}
        
        Контактная информация: {contact_info or 'Не указана'}
        
        Ссылка на ошибку: {request.build_absolute_uri('/admin/calculation/errorlog/')}
        """
        
        # Only send email in production
        try:
            mail_admins(subject, message, fail_silently=True)
        except:
            pass
            
        messages.success(request, 'Ваш отчет успешно отправлен. Спасибо за помощь!')
        return redirect('index')
        
    return render(request, 'calculation/report_error.html', {
        'error_log': error_log
    })


@user_passes_test(lambda u: u.is_staff)
def error_list(request):
    """
    View to list all errors (for staff)
    """
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'resolved':
        error_logs = ErrorLog.objects.filter(resolved=True)
    elif status_filter == 'unresolved':
        error_logs = ErrorLog.objects.filter(resolved=False)
    else:
        error_logs = ErrorLog.objects.all()
    
    # Pagination
    paginator = Paginator(error_logs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'calculation/error_list.html', {
        'error_logs': page_obj,
        'status': status_filter
    })


@user_passes_test(lambda u: u.is_staff)
def view_error(request, error_id):
    """
    View to see detailed error information (for staff)
    """
    try:
        error_log = ErrorLog.objects.get(id=error_id)
    except ErrorLog.DoesNotExist:
        raise Http404("Ошибка не найдена")
        
    error_reports = error_log.user_reports.all()
    
    return render(request, 'calculation/error_detail.html', {
        'error_log': error_log,
        'error_reports': error_reports
    })


@user_passes_test(lambda u: u.is_staff)
def resolve_error(request, error_id):
    """
    View to mark an error as resolved
    """
    error_log = get_object_or_404(ErrorLog, id=error_id)
    
    if request.method == 'POST':
        resolution_notes = request.POST.get('resolution_notes', '')
        error_log.resolved = True
        error_log.resolution_notes = resolution_notes
        error_log.save()
        
        messages.success(request, f'Ошибка #{error_id} помечена как решенная')
        
        # Redirect back to the error list
        return redirect('view_error', error_id=error_id)
        
    # If not POST, redirect to the error detail view
    return redirect('view_error', error_id=error_id)
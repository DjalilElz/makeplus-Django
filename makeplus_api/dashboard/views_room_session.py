
# ==================== Room Management ====================

@login_required
@user_passes_test(is_staff_user)
def room_create(request, event_id):
    """Create a new room for an event"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.event = event
            room.save()
            messages.success(request, f'Room "{room.name}" created successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = RoomForm()
    
    context = {
        'form': form,
        'event': event,
        'is_edit': False
    }
    
    return render(request, 'dashboard/room_edit.html', context)


@login_required
@user_passes_test(is_staff_user)
def room_edit(request, room_id):
    """Edit an existing room"""
    room = get_object_or_404(Room, id=room_id)
    event = room.event
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f'Room "{room.name}" updated successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = RoomForm(instance=room)
    
    context = {
        'form': form,
        'room': room,
        'event': event,
        'is_edit': True
    }
    
    return render(request, 'dashboard/room_edit.html', context)


@login_required
@user_passes_test(is_staff_user)
def room_delete(request, room_id):
    """Delete a room"""
    room = get_object_or_404(Room, id=room_id)
    event_id = room.event.id
    room_name = room.name
    
    if request.method == 'POST':
        room.delete()
        messages.success(request, f'Room "{room_name}" deleted successfully!')
        return redirect('dashboard:event_detail', event_id=event_id)
    
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:event_detail', event_id=event_id)


# ==================== Session Management ====================

@login_required
@user_passes_test(is_staff_user)
def session_create(request, event_id):
    """Create a new session for an event"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = SessionForm(request.POST, event=event)
        if form.is_valid():
            session = form.save(commit=False)
            session.event = event
            session.save()
            messages.success(request, f'Session "{session.title}" created successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = SessionForm(event=event)
    
    context = {
        'form': form,
        'event': event,
        'is_edit': False
    }
    
    return render(request, 'dashboard/session_edit.html', context)


@login_required
@user_passes_test(is_staff_user)
def session_edit(request, session_id):
    """Edit an existing session"""
    session = get_object_or_404(Session, id=session_id)
    event = session.event
    
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session, event=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Session "{session.title}" updated successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = SessionForm(instance=session, event=event)
    
    context = {
        'form': form,
        'session': session,
        'event': event,
        'is_edit': True
    }
    
    return render(request, 'dashboard/session_edit.html', context)


@login_required
@user_passes_test(is_staff_user)
def session_delete(request, session_id):
    """Delete a session"""
    session = get_object_or_404(Session, id=session_id)
    event_id = session.event.id
    session_title = session.title
    
    if request.method == 'POST':
        session.delete()
        messages.success(request, f'Session "{session_title}" deleted successfully!')
        return redirect('dashboard:event_detail', event_id=event_id)
    
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:event_detail', event_id=event_id)

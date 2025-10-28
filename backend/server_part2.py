# Continuação do server.py - Parte 2

# ===== SCHEDULE ROUTES =====

@api_router.get("/schedules", response_model=List[EscalaResponse])
async def get_schedules(
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    id_igreja: Optional[str] = None,
    id_distrito: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Escala)
    
    if current_user.funcao != 'pastor_distrital':
        query = query.filter(Escala.id_distrito == current_user.id_distrito)
    
    if mes:
        query = query.filter(Escala.mes == mes)
    if ano:
        query = query.filter(Escala.ano == ano)
    if id_igreja:
        query = query.filter(Escala.id_igreja == id_igreja)
    if id_distrito:
        query = query.filter(Escala.id_distrito == id_distrito)
    
    escalas = query.all()
    
    # Carregar itens para cada escala
    result = []
    for escala in escalas:
        itens = db.query(ItemEscala).filter(ItemEscala.id_escala == escala.id).all()
        escala_dict = {
            "id": escala.id,
            "mes": escala.mes,
            "ano": escala.ano,
            "id_igreja": escala.id_igreja,
            "id_distrito": escala.id_distrito,
            "id_gerado_por": escala.id_gerado_por,
            "modo_geracao": escala.modo_geracao,
            "status": escala.status,
            "criado_em": escala.criado_em,
            "atualizado_em": escala.atualizado_em,
            "itens": [ItemEscalaData(
                id=item.id,
                data=item.data,
                horario=item.horario,
                id_pregador=item.id_pregador,
                ids_cantores=item.ids_cantores or [],
                status=item.status,
                motivo_recusa=item.motivo_recusa,
                confirmado_em=item.confirmado_em,
                cancelado_em=item.cancelado_em
            ) for item in itens]
        }
        result.append(EscalaResponse(**escala_dict))
    
    return result

@api_router.post("/schedules/generate-auto")
async def generate_schedule_auto(
    mes: int,
    ano: int,
    id_distrito: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Get all churches in district
    igrejas = db.query(Igreja).filter(Igreja.id_distrito == id_distrito, Igreja.ativo == True).all()
    
    # Get all preachers and singers in district
    pregadores = db.query(Usuario).filter(
        Usuario.id_distrito == id_distrito,
        Usuario.eh_pregador == True,
        Usuario.ativo == True
    ).order_by(Usuario.pontuacao_pregacao.desc()).all()
    
    escalas_geradas = []
    
    for igreja in igrejas:
        # Check if schedule already exists
        existing = db.query(Escala).filter(
            Escala.id_igreja == igreja.id,
            Escala.mes == mes,
            Escala.ano == ano
        ).first()
        if existing:
            continue
        
        # Create schedule
        escala = Escala(
            mes=mes,
            ano=ano,
            id_igreja=igreja.id,
            id_distrito=id_distrito,
            id_gerado_por=current_user.id,
            modo_geracao='automatico',
            status='rascunho'
        )
        db.add(escala)
        db.flush()
        
        # Generate items for all days in the month
        horarios_culto = igreja.horarios_culto or []
        if not horarios_culto:
            continue
        
        _, num_dias = calendar.monthrange(ano, mes)
        
        pregador_index = 0
        for dia in range(1, num_dias + 1):
            date_obj = datetime(ano, mes, dia)
            dia_semana = date_obj.strftime('%A').lower()
            dia_semana_map = {
                'monday': 'segunda',
                'tuesday': 'terca',
                'wednesday': 'quarta',
                'thursday': 'quinta',
                'friday': 'sexta',
                'saturday': 'sabado',
                'sunday': 'domingo'
            }
            dia_semana_pt = dia_semana_map.get(dia_semana, dia_semana)
            
            # Check if this day has a service
            horario_encontrado = None
            for horario in horarios_culto:
                if horario.get('dia_semana', '').lower() in [dia_semana, dia_semana_pt]:
                    horario_encontrado = horario
                    break
            
            if horario_encontrado:
                data_str = date_obj.strftime('%Y-%m-%d')
                
                # Select preacher (rotating)
                pregador = None
                tentativas = 0
                while tentativas < len(pregadores):
                    candidato = pregadores[pregador_index % len(pregadores)]
                    pregador_index += 1
                    tentativas += 1
                    
                    if usuario_disponivel(db, candidato.id, data_str) and not slot_ocupado(db, candidato.id, data_str):
                        pregador = candidato
                        break
                
                if pregador:
                    item = ItemEscala(
                        id_escala=escala.id,
                        data=data_str,
                        horario=horario_encontrado.get('horario', ''),
                        id_pregador=pregador.id,
                        ids_cantores=[],
                        status='pendente'
                    )
                    db.add(item)
        
        escalas_geradas.append(escala)
    
    db.commit()
    
    return {"message": f"Geradas {len(escalas_geradas)} escalas", "escalas": [e.id for e in escalas_geradas]}

@api_router.post("/schedules/manual", response_model=EscalaResponse)
async def create_manual_schedule(
    schedule_data: EscalaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Check if schedule already exists
    existing = db.query(Escala).filter(
        Escala.id_igreja == schedule_data.id_igreja,
        Escala.mes == schedule_data.mes,
        Escala.ano == schedule_data.ano
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Schedule already exists for this month/year")
    
    # Get church info
    igreja = db.query(Igreja).filter(Igreja.id == schedule_data.id_igreja).first()
    if not igreja:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Create empty schedule
    escala = Escala(
        mes=schedule_data.mes,
        ano=schedule_data.ano,
        id_igreja=schedule_data.id_igreja,
        id_distrito=igreja.id_distrito,
        id_gerado_por=current_user.id,
        modo_geracao='manual',
        status='rascunho'
    )
    db.add(escala)
    db.flush()
    
    # Create empty items for service days
    horarios_culto = igreja.horarios_culto or []
    _, num_dias = calendar.monthrange(schedule_data.ano, schedule_data.mes)
    
    for dia in range(1, num_dias + 1):
        date_obj = datetime(schedule_data.ano, schedule_data.mes, dia)
        dia_semana = date_obj.strftime('%A').lower()
        
        horario_encontrado = None
        for horario in horarios_culto:
            if horario.get('dia_semana', '').lower() == dia_semana:
                horario_encontrado = horario
                break
        
        if horario_encontrado:
            item = ItemEscala(
                id_escala=escala.id,
                data=date_obj.strftime('%Y-%m-%d'),
                horario=horario_encontrado.get('horario', ''),
                id_pregador=None,
                ids_cantores=[],
                status='pendente'
            )
            db.add(item)
    
    db.commit()
    db.refresh(escala)
    
    # Load items
    itens = db.query(ItemEscala).filter(ItemEscala.id_escala == escala.id).all()
    
    return EscalaResponse(
        id=escala.id,
        mes=escala.mes,
        ano=escala.ano,
        id_igreja=escala.id_igreja,
        id_distrito=escala.id_distrito,
        id_gerado_por=escala.id_gerado_por,
        modo_geracao=escala.modo_geracao,
        status=escala.status,
        criado_em=escala.criado_em,
        atualizado_em=escala.atualizado_em,
        itens=[ItemEscalaData(
            id=item.id,
            data=item.data,
            horario=item.horario,
            id_pregador=item.id_pregador,
            ids_cantores=item.ids_cantores or [],
            status=item.status,
            motivo_recusa=item.motivo_recusa,
            confirmado_em=item.confirmado_em,
            cancelado_em=item.cancelado_em
        ) for item in itens]
    )

@api_router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    escala = db.query(Escala).filter(Escala.id == schedule_id).first()
    if not escala:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    itens = db.query(ItemEscala).filter(ItemEscala.id_escala == escala.id).all()
    
    return EscalaResponse(
        id=escala.id,
        mes=escala.mes,
        ano=escala.ano,
        id_igreja=escala.id_igreja,
        id_distrito=escala.id_distrito,
        id_gerado_por=escala.id_gerado_por,
        modo_geracao=escala.modo_geracao,
        status=escala.status,
        criado_em=escala.criado_em,
        atualizado_em=escala.atualizado_em,
        itens=[ItemEscalaData(
            id=item.id,
            data=item.data,
            horario=item.horario,
            id_pregador=item.id_pregador,
            ids_cantores=item.ids_cantores or [],
            status=item.status,
            motivo_recusa=item.motivo_recusa,
            confirmado_em=item.confirmado_em,
            cancelado_em=item.cancelado_em
        ) for item in itens]
    )

@api_router.put("/schedules/{schedule_id}/items/{item_id}")
async def update_schedule_item(
    schedule_id: str,
    item_id: str,
    id_pregador: Optional[str] = None,
    ids_cantores: Optional[List[str]] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id, ItemEscala.id_escala == schedule_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    if id_pregador is not None:
        if slot_ocupado(db, id_pregador, item.data):
            raise HTTPException(status_code=400, detail="Preacher already scheduled on this date")
        item.id_pregador = id_pregador
    
    if ids_cantores is not None:
        for cantor_id in ids_cantores:
            if slot_ocupado(db, cantor_id, item.data):
                raise HTTPException(status_code=400, detail=f"Singer {cantor_id} already scheduled on this date")
        item.ids_cantores = ids_cantores
    
    item.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "Schedule item updated"}

@api_router.post("/schedules/{schedule_id}/confirm")
async def confirm_schedule(
    schedule_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    escala = db.query(Escala).filter(Escala.id == schedule_id).first()
    if not escala:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Check if all items have preachers
    itens = db.query(ItemEscala).filter(ItemEscala.id_escala == schedule_id).all()
    for item in itens:
        if not item.id_pregador:
            raise HTTPException(status_code=400, detail=f"Item on {item.data} has no preacher assigned")
    
    escala.status = 'confirmada'
    escala.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    
    # Send notifications
    igreja = db.query(Igreja).filter(Igreja.id == escala.id_igreja).first()
    
    for item in itens:
        if item.id_pregador:
            pregador = db.query(Usuario).filter(Usuario.id == item.id_pregador).first()
            if pregador:
                mensagem = f"Você foi escalado para pregar em {igreja.nome} no dia {item.data} às {item.horario}"
                criar_notificacao(
                    db,
                    pregador.id,
                    'atribuicao_escala',
                    'Nova Escala de Pregação',
                    mensagem,
                    item.id
                )
                if pregador.telefone:
                    enviar_notificacao_mock(pregador.telefone, mensagem)
        
        for cantor_id in (item.ids_cantores or []):
            cantor = db.query(Usuario).filter(Usuario.id == cantor_id).first()
            if cantor:
                mensagem = f"Você foi escalado para Louvor Especial em {igreja.nome} no dia {item.data} às {item.horario}"
                criar_notificacao(
                    db,
                    cantor.id,
                    'atribuicao_escala',
                    'Nova Escala de Louvor',
                    mensagem,
                    item.id
                )
                if cantor.telefone:
                    enviar_notificacao_mock(cantor.telefone, mensagem)
    
    return {"message": "Schedule confirmed and notifications sent"}

@api_router.post("/schedule-items/{item_id}/confirm")
async def confirm_participation(item_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    if item.id_pregador != current_user.id and current_user.id not in (item.ids_cantores or []):
        raise HTTPException(status_code=403, detail="You are not assigned to this schedule")
    
    item.status = 'confirmado'
    item.confirmado_em = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "Participation confirmed"}

@api_router.post("/schedule-items/{item_id}/refuse")
async def refuse_participation(item_id: str, motivo: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    escala = db.query(Escala).filter(Escala.id == item.id_escala).first()
    igreja = db.query(Igreja).filter(Igreja.id == escala.id_igreja).first()
    distrito = db.query(Distrito).filter(Distrito.id == escala.id_distrito).first()
    
    tipo_membro = 'pregador' if item.id_pregador == current_user.id else 'cantor'
    
    if item.id_pregador == current_user.id:
        item.id_pregador = None
    elif current_user.id in (item.ids_cantores or []):
        item.ids_cantores.remove(current_user.id)
    else:
        raise HTTPException(status_code=403, detail="You are not assigned to this schedule")
    
    item.status = 'recusado'
    item.motivo_recusa = motivo
    db.commit()
    
    # Notify pastor
    pastor = db.query(Usuario).filter(Usuario.id == distrito.id_pastor).first()
    if pastor:
        mensagem = f"{current_user.nome_completo} ({tipo_membro}) recusou a escala em {igreja.nome} no dia {item.data} às {item.horario}. Motivo: {motivo}"
        criar_notificacao(db, pastor.id, 'recusa_escala', 'Recusa de Escala', mensagem, item_id)
        if pastor.telefone:
            enviar_notificacao_mock(pastor.telefone, mensagem)
    
    # Notify church leader
    if igreja.id_lider:
        lider = db.query(Usuario).filter(Usuario.id == igreja.id_lider).first()
        if lider:
            criar_notificacao(db, lider.id, 'recusa_escala', 'Recusa de Escala', mensagem, item_id)
    
    return {"message": "Participation refused"}

@api_router.post("/schedule-items/{item_id}/cancel")
async def cancel_participation(item_id: str, motivo: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    # Check if within 2 days
    item_date = datetime.fromisoformat(item.data)
    days_until = (item_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days
    
    if days_until < 2:
        raise HTTPException(status_code=400, detail="Cannot cancel within 2 days of the service")
    
    if item.status != 'confirmado':
        raise HTTPException(status_code=400, detail="Can only cancel confirmed participation")
    
    item.status = 'cancelado'
    item.cancelado_em = datetime.now(timezone.utc)
    item.motivo_recusa = motivo
    
    if item.id_pregador == current_user.id:
        item.id_pregador = None
    elif current_user.id in (item.ids_cantores or []):
        item.ids_cantores.remove(current_user.id)
    
    db.commit()
    
    return {"message": "Participation cancelled"}

@api_router.post("/schedule-items/{item_id}/volunteer")
async def volunteer_for_slot(item_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    if item.id_pregador:
        raise HTTPException(status_code=400, detail="Slot is already filled")
    
    if not usuario_disponivel(db, current_user.id, item.data):
        raise HTTPException(status_code=400, detail="You are not available on this date")
    
    if slot_ocupado(db, current_user.id, item.data):
        raise HTTPException(status_code=400, detail="You are already scheduled on this date")
    
    if current_user.eh_pregador:
        item.id_pregador = current_user.id
        item.status = 'confirmado'
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="You must be a preacher to volunteer")
    
    return {"message": "Successfully volunteered for slot"}

@api_router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    escala = db.query(Escala).filter(Escala.id == schedule_id).first()
    if escala:
        db.query(ItemEscala).filter(ItemEscala.id_escala == schedule_id).delete()
        db.delete(escala)
        db.commit()
    
    return {"message": "Schedule deleted successfully"}

# Continue no arquivo final...

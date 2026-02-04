"""Fixed deposit management API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.fixed_deposit import FixedDeposit
from app.schemas import (
    FixedDepositCreate,
    FixedDepositResponse,
    FixedDepositUpdate,
    FixedDepositWithValue,
    InterestCalculationRequest,
    InterestCalculationResponse,
)
from app.services.interest_calculator import calculate_current_value

router = APIRouter(prefix='/api/v1/fixed-deposits', tags=['Fixed Deposits'])


@router.post('', response_model=FixedDepositResponse, status_code=status.HTTP_201_CREATED)
async def create_fixed_deposit(
    fixed_deposit: FixedDepositCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new fixed deposit.

    Args:
        fixed_deposit: Fixed deposit data to create.
        db: Database session.

    Returns:
        FixedDepositResponse: Created fixed deposit.

    Raises:
        HTTPException: If validation fails.
    """
    db_fixed_deposit = FixedDeposit(**fixed_deposit.model_dump())
    db.add(db_fixed_deposit)
    await db.commit()
    await db.refresh(db_fixed_deposit)
    return db_fixed_deposit


@router.get('', response_model=list[FixedDepositWithValue])
async def list_fixed_deposits(
    status_filter: str | None = Query(
        None, alias='status', description="Filter by status: 'all', 'active', 'matured'"
    ),
    institution: str | None = Query(None, description='Filter by institution name'),
    db: AsyncSession = Depends(get_db),
):
    """List all fixed deposits with current values.

    Args:
        status_filter: Filter by status (all/active/matured).
        institution: Filter by institution name.
        db: Database session.

    Returns:
        List of fixed deposits with calculated current values.
    """
    query = select(FixedDeposit).order_by(FixedDeposit.maturity_date.asc())

    # Apply institution filter
    if institution:
        query = query.where(FixedDeposit.institution_name.ilike(f'%{institution}%'))

    result = await db.execute(query)
    fixed_deposits = result.scalars().all()

    # Calculate current values and filter by status
    now = datetime.now(timezone.utc)
    fd_list = []

    for fd in fixed_deposits:
        current_value, accrued_interest, days_to_maturity = calculate_current_value(
            principal=fd.principal_amount,
            annual_rate=fd.interest_rate,
            start_date=fd.start_date,
            maturity_date=fd.maturity_date,
            calculation_type=fd.interest_calculation_type,
            payout_frequency=fd.interest_payout_frequency,
            as_of_date=now,
        )

        is_matured = days_to_maturity <= 0
        term_days = (fd.maturity_date - fd.start_date).days

        # Apply status filter
        if status_filter == 'active' and is_matured:
            continue
        elif status_filter == 'matured' and not is_matured:
            continue

        fd_list.append(
            FixedDepositWithValue(
                id=fd.id,
                principal_amount=fd.principal_amount,
                interest_rate=fd.interest_rate,
                start_date=fd.start_date,
                maturity_date=fd.maturity_date,
                institution_name=fd.institution_name,
                account_number=fd.account_number,
                interest_payout_frequency=fd.interest_payout_frequency,
                interest_calculation_type=fd.interest_calculation_type,
                auto_renewal=fd.auto_renewal,
                notes=fd.notes,
                created_at=fd.created_at,
                updated_at=fd.updated_at,
                current_value=current_value,
                accrued_interest=accrued_interest,
                days_to_maturity=days_to_maturity,
                is_matured=is_matured,
                term_days=term_days,
            )
        )

    return fd_list


@router.get('/{fixed_deposit_id}', response_model=FixedDepositWithValue)
async def get_fixed_deposit(fixed_deposit_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific fixed deposit by ID with current value.

    Args:
        fixed_deposit_id: Fixed deposit ID.
        db: Database session.

    Returns:
        FixedDepositWithValue: Fixed deposit data with calculated values.

    Raises:
        HTTPException: If fixed deposit not found.
    """
    result = await db.execute(select(FixedDeposit).where(FixedDeposit.id == fixed_deposit_id))
    fd = result.scalar_one_or_none()
    if not fd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Fixed deposit not found'
        )

    now = datetime.now(timezone.utc)
    current_value, accrued_interest, days_to_maturity = calculate_current_value(
        principal=fd.principal_amount,
        annual_rate=fd.interest_rate,
        start_date=fd.start_date,
        maturity_date=fd.maturity_date,
        calculation_type=fd.interest_calculation_type,
        payout_frequency=fd.interest_payout_frequency,
        as_of_date=now,
    )

    is_matured = days_to_maturity <= 0
    term_days = (fd.maturity_date - fd.start_date).days

    return FixedDepositWithValue(
        id=fd.id,
        principal_amount=fd.principal_amount,
        interest_rate=fd.interest_rate,
        start_date=fd.start_date,
        maturity_date=fd.maturity_date,
        institution_name=fd.institution_name,
        account_number=fd.account_number,
        interest_payout_frequency=fd.interest_payout_frequency,
        interest_calculation_type=fd.interest_calculation_type,
        auto_renewal=fd.auto_renewal,
        notes=fd.notes,
        created_at=fd.created_at,
        updated_at=fd.updated_at,
        current_value=current_value,
        accrued_interest=accrued_interest,
        days_to_maturity=days_to_maturity,
        is_matured=is_matured,
        term_days=term_days,
    )


@router.put('/{fixed_deposit_id}', response_model=FixedDepositResponse)
async def update_fixed_deposit(
    fixed_deposit_id: int,
    fixed_deposit: FixedDepositUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a fixed deposit.

    Args:
        fixed_deposit_id: Fixed deposit ID.
        fixed_deposit: Updated fixed deposit data.
        db: Database session.

    Returns:
        FixedDepositResponse: Updated fixed deposit.

    Raises:
        HTTPException: If fixed deposit not found or validation fails.
    """
    result = await db.execute(select(FixedDeposit).where(FixedDeposit.id == fixed_deposit_id))
    db_fixed_deposit = result.scalar_one_or_none()
    if not db_fixed_deposit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Fixed deposit not found'
        )

    update_data = fixed_deposit.model_dump(exclude_unset=True)

    # Validate date relationship if both are being updated
    start_date = update_data.get('start_date', db_fixed_deposit.start_date)
    maturity_date = update_data.get('maturity_date', db_fixed_deposit.maturity_date)

    if maturity_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Maturity date must be after start date',
        )

    for field, value in update_data.items():
        setattr(db_fixed_deposit, field, value)

    await db.commit()
    await db.refresh(db_fixed_deposit)
    return db_fixed_deposit


@router.delete('/{fixed_deposit_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_fixed_deposit(fixed_deposit_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a fixed deposit.

    Args:
        fixed_deposit_id: Fixed deposit ID.
        db: Database session.

    Raises:
        HTTPException: If fixed deposit not found.
    """
    result = await db.execute(select(FixedDeposit).where(FixedDeposit.id == fixed_deposit_id))
    db_fixed_deposit = result.scalar_one_or_none()
    if not db_fixed_deposit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Fixed deposit not found'
        )

    await db.delete(db_fixed_deposit)
    await db.commit()
    return None


@router.post('/calculate-interest', response_model=InterestCalculationResponse)
async def calculate_interest(request: InterestCalculationRequest):
    """Calculate interest for given parameters (utility endpoint).

    This endpoint calculates interest values without creating a fixed deposit.
    Useful for previewing calculations in the UI.

    Args:
        request: Interest calculation parameters.

    Returns:
        InterestCalculationResponse: Calculated interest values.

    Raises:
        HTTPException: If validation fails.
    """
    if request.maturity_date <= request.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Maturity date must be after start date',
        )

    now = datetime.now(timezone.utc)
    term_days = (request.maturity_date - request.start_date).days
    days_elapsed = (now - request.start_date).days

    # Calculate at maturity
    maturity_value, total_interest, _ = calculate_current_value(
        principal=request.principal,
        annual_rate=request.annual_rate,
        start_date=request.start_date,
        maturity_date=request.maturity_date,
        calculation_type=request.calculation_type,
        payout_frequency=request.payout_frequency,
        as_of_date=request.maturity_date,
    )

    # Calculate current values
    current_value, current_interest, days_remaining = calculate_current_value(
        principal=request.principal,
        annual_rate=request.annual_rate,
        start_date=request.start_date,
        maturity_date=request.maturity_date,
        calculation_type=request.calculation_type,
        payout_frequency=request.payout_frequency,
        as_of_date=now,
    )

    return InterestCalculationResponse(
        total_interest=total_interest,
        maturity_value=maturity_value,
        term_days=term_days,
        current_interest=current_interest,
        current_value=current_value,
        days_elapsed=max(0, days_elapsed),
        days_remaining=days_remaining,
    )

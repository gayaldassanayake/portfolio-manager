import { useState, useEffect } from 'react';
import { Modal, ModalFooter, Button, Input, Select, Textarea } from '../ui';
import { useCreateFixedDeposit, useUpdateFixedDeposit } from '../../api/hooks';
import type {
  FixedDeposit,
  FixedDepositCreate,
  InterestPayoutFrequency,
  InterestCalculationType,
} from '../../types';
import styles from './FixedDepositFormModal.module.css';

interface FixedDepositFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  fixedDeposit?: FixedDeposit; // If provided, edit mode; otherwise create mode
  onSuccess?: () => void;
}

interface FormData {
  principal_amount: string;
  interest_rate: string;
  start_date: string;
  maturity_date: string;
  institution_name: string;
  account_number: string;
  interest_payout_frequency: InterestPayoutFrequency;
  interest_calculation_type: InterestCalculationType;
  auto_renewal: boolean;
  notes: string;
}

type DateInputMode = 'date' | 'duration';
type DurationUnit = 'days' | 'months' | 'years';

const PAYOUT_FREQUENCY_OPTIONS = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'annually', label: 'Annually' },
  { value: 'at_maturity', label: 'At Maturity' },
];

const CALCULATION_TYPE_OPTIONS = [
  { value: 'simple', label: 'Simple Interest' },
  { value: 'compound', label: 'Compound Interest' },
];

export function FixedDepositFormModal({
  isOpen,
  onClose,
  fixedDeposit,
  onSuccess,
}: FixedDepositFormModalProps) {
  const isEditMode = !!fixedDeposit;
  const createMutation = useCreateFixedDeposit();
  const updateMutation = useUpdateFixedDeposit();

  const [formData, setFormData] = useState<FormData>({
    principal_amount: '',
    interest_rate: '',
    start_date: '',
    maturity_date: '',
    institution_name: '',
    account_number: '',
    interest_payout_frequency: 'at_maturity',
    interest_calculation_type: 'simple',
    auto_renewal: false,
    notes: '',
  });

  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [dateInputMode, setDateInputMode] = useState<DateInputMode>('date');
  const [durationValue, setDurationValue] = useState<string>('');
  const [durationUnit, setDurationUnit] = useState<DurationUnit>('months');

  // Helper function to calculate maturity date from duration
  const calculateMaturityFromDuration = (
    startDate: string,
    value: number,
    unit: DurationUnit
  ): string => {
    if (!startDate || !value) return '';

    const start = new Date(startDate);
    const result = new Date(start);

    if (unit === 'days') {
      result.setDate(result.getDate() + value);
    } else if (unit === 'months') {
      result.setMonth(result.getMonth() + value);
    } else if (unit === 'years') {
      result.setFullYear(result.getFullYear() + value);
    }

    return result.toISOString().split('T')[0];
  };

  // Helper function to calculate duration from dates (approximate)
  const calculateDurationFromDates = (
    startDate: string,
    maturityDate: string
  ): { value: number; unit: DurationUnit } => {
    if (!startDate || !maturityDate) return { value: 0, unit: 'months' };

    const start = new Date(startDate);
    const end = new Date(maturityDate);
    const diffMs = end.getTime() - start.getTime();
    const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

    // Try to express in the most convenient unit
    const years = Math.round(diffDays / 365);
    const months = Math.round(diffDays / 30);

    if (years > 0 && diffDays % 365 < 30) {
      return { value: years, unit: 'years' };
    } else if (months > 0 && diffDays % 30 < 7) {
      return { value: months, unit: 'months' };
    } else {
      return { value: diffDays, unit: 'days' };
    }
  };

  // Initialize form with fixed deposit data in edit mode
  useEffect(() => {
    if (fixedDeposit) {
      const startDate = fixedDeposit.start_date.split('T')[0];
      const maturityDate = fixedDeposit.maturity_date.split('T')[0];

      setFormData({
        principal_amount: fixedDeposit.principal_amount.toString(),
        interest_rate: fixedDeposit.interest_rate.toString(),
        start_date: startDate,
        maturity_date: maturityDate,
        institution_name: fixedDeposit.institution_name,
        account_number: fixedDeposit.account_number,
        interest_payout_frequency: fixedDeposit.interest_payout_frequency,
        interest_calculation_type: fixedDeposit.interest_calculation_type,
        auto_renewal: fixedDeposit.auto_renewal,
        notes: fixedDeposit.notes || '',
      });

      // Calculate duration from dates for display
      const duration = calculateDurationFromDates(startDate, maturityDate);
      setDurationValue(duration.value.toString());
      setDurationUnit(duration.unit);
    } else {
      setFormData({
        principal_amount: '',
        interest_rate: '',
        start_date: '',
        maturity_date: '',
        institution_name: '',
        account_number: '',
        interest_payout_frequency: 'at_maturity',
        interest_calculation_type: 'simple',
        auto_renewal: false,
        notes: '',
      });
      setDurationValue('');
      setDurationUnit('months');
    }
    setErrors({});
    setDateInputMode('date'); // Reset to date mode on open
  }, [fixedDeposit, isOpen]);

  const handleChange = (field: keyof FormData, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }

    // If start date changes and we're in duration mode, recalculate maturity date
    if (field === 'start_date' && dateInputMode === 'duration' && durationValue) {
      const maturity = calculateMaturityFromDuration(
        value as string,
        parseInt(durationValue),
        durationUnit
      );
      if (maturity) {
        setFormData((prev) => ({ ...prev, maturity_date: maturity }));
      }
    }
  };

  const handleDurationValueChange = (value: string) => {
    setDurationValue(value);
    const numValue = parseInt(value);

    if (formData.start_date && numValue > 0) {
      const maturity = calculateMaturityFromDuration(formData.start_date, numValue, durationUnit);
      if (maturity) {
        setFormData((prev) => ({ ...prev, maturity_date: maturity }));
      }
    }
  };

  const handleDurationUnitChange = (unit: DurationUnit) => {
    setDurationUnit(unit);
    const numValue = parseInt(durationValue);

    if (formData.start_date && numValue > 0) {
      const maturity = calculateMaturityFromDuration(formData.start_date, numValue, unit);
      if (maturity) {
        setFormData((prev) => ({ ...prev, maturity_date: maturity }));
      }
    }
  };

  const handleDateInputModeChange = (mode: DateInputMode) => {
    setDateInputMode(mode);

    // When switching to duration mode, calculate duration from current dates
    if (mode === 'duration' && formData.start_date && formData.maturity_date) {
      const duration = calculateDurationFromDates(formData.start_date, formData.maturity_date);
      setDurationValue(duration.value.toString());
      setDurationUnit(duration.unit);
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    const principal = parseFloat(formData.principal_amount);
    if (!formData.principal_amount.trim() || isNaN(principal) || principal <= 0) {
      newErrors.principal_amount = 'Principal amount must be greater than 0';
    }

    const rate = parseFloat(formData.interest_rate);
    if (!formData.interest_rate.trim() || isNaN(rate) || rate < 0 || rate > 100) {
      newErrors.interest_rate = 'Interest rate must be between 0 and 100';
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    if (!formData.maturity_date) {
      newErrors.maturity_date = 'Maturity date is required';
    }

    // Validate maturity date is after start date
    if (formData.start_date && formData.maturity_date) {
      const startDate = new Date(formData.start_date);
      const maturityDate = new Date(formData.maturity_date);
      if (maturityDate <= startDate) {
        newErrors.maturity_date = 'Maturity date must be after start date';
      }
    }

    if (!formData.institution_name.trim()) {
      newErrors.institution_name = 'Institution name is required';
    }

    if (!formData.account_number.trim()) {
      newErrors.account_number = 'Account number is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    try {
      // Convert dates to ISO format with timezone
      const startDate = new Date(formData.start_date);
      const maturityDate = new Date(formData.maturity_date);

      const payload = {
        principal_amount: parseFloat(formData.principal_amount),
        interest_rate: parseFloat(formData.interest_rate),
        start_date: startDate.toISOString(),
        maturity_date: maturityDate.toISOString(),
        institution_name: formData.institution_name.trim(),
        account_number: formData.account_number.trim(),
        interest_payout_frequency: formData.interest_payout_frequency,
        interest_calculation_type: formData.interest_calculation_type,
        auto_renewal: formData.auto_renewal,
        notes: formData.notes.trim() || null,
      };

      if (isEditMode && fixedDeposit) {
        // Update mode
        await updateMutation.mutateAsync({ id: fixedDeposit.id, data: payload });
      } else {
        // Create mode
        await createMutation.mutateAsync(payload as FixedDepositCreate);
      }

      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to save fixed deposit:', error);
      // Error handling can be enhanced with toast notifications
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? 'Edit Fixed Deposit' : 'Add New Fixed Deposit'}
      description={
        isEditMode
          ? 'Update the fixed deposit details'
          : 'Create a new fixed deposit with interest calculation'
      }
      size="lg"
    >
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.grid}>
          {/* Principal Amount */}
          <Input
            label="Principal Amount"
            type="number"
            step="0.01"
            placeholder="e.g., 10000"
            value={formData.principal_amount}
            onChange={(e) => handleChange('principal_amount', e.target.value)}
            error={errors.principal_amount}
            disabled={isPending}
            required
          />

          {/* Interest Rate */}
          <Input
            label="Interest Rate (%)"
            type="number"
            step="0.01"
            placeholder="e.g., 8.5"
            value={formData.interest_rate}
            onChange={(e) => handleChange('interest_rate', e.target.value)}
            error={errors.interest_rate}
            disabled={isPending}
            required
          />

          {/* Start Date */}
          <Input
            label="Start Date"
            type="date"
            value={formData.start_date}
            onChange={(e) => handleChange('start_date', e.target.value)}
            error={errors.start_date}
            disabled={isPending}
            required
          />

          {/* Maturity Date / Duration Input */}
          <div className={styles.fullWidth}>
            <div className={styles.dateInputToggle}>
              <label className={styles.label}>Maturity</label>
              <div className={styles.toggleButtons}>
                <button
                  type="button"
                  className={`${styles.toggleButton} ${
                    dateInputMode === 'date' ? styles.toggleButtonActive : ''
                  }`}
                  onClick={() => handleDateInputModeChange('date')}
                  disabled={isPending}
                >
                  Date
                </button>
                <button
                  type="button"
                  className={`${styles.toggleButton} ${
                    dateInputMode === 'duration' ? styles.toggleButtonActive : ''
                  }`}
                  onClick={() => handleDateInputModeChange('duration')}
                  disabled={isPending}
                >
                  Duration
                </button>
              </div>
            </div>

            {dateInputMode === 'date' ? (
              <Input
                type="date"
                value={formData.maturity_date}
                onChange={(e) => handleChange('maturity_date', e.target.value)}
                error={errors.maturity_date}
                disabled={isPending}
                required
              />
            ) : (
              <div className={styles.durationInputs}>
                <Input
                  type="number"
                  placeholder="e.g., 6"
                  value={durationValue}
                  onChange={(e) => handleDurationValueChange(e.target.value)}
                  error={errors.maturity_date}
                  disabled={isPending}
                  required
                  className={styles.durationValue}
                />
                <Select
                  options={[
                    { value: 'days', label: 'Days' },
                    { value: 'months', label: 'Months' },
                    { value: 'years', label: 'Years' },
                  ]}
                  value={durationUnit}
                  onChange={(e) => handleDurationUnitChange(e.target.value as DurationUnit)}
                  disabled={isPending}
                  className={styles.durationUnit}
                />
                {formData.maturity_date && (
                  <div className={styles.calculatedDate}>
                    Maturity: {new Date(formData.maturity_date).toLocaleDateString()}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Institution Name */}
          <Input
            label="Institution Name"
            placeholder="e.g., ABC Bank"
            value={formData.institution_name}
            onChange={(e) => handleChange('institution_name', e.target.value)}
            error={errors.institution_name}
            disabled={isPending}
            required
          />

          {/* Account Number */}
          <Input
            label="Account Number"
            placeholder="e.g., FD-12345"
            value={formData.account_number}
            onChange={(e) => handleChange('account_number', e.target.value)}
            error={errors.account_number}
            disabled={isPending}
            required
          />

          {/* Interest Calculation Type */}
          <Select
            label="Interest Calculation Type"
            options={CALCULATION_TYPE_OPTIONS}
            value={formData.interest_calculation_type}
            onChange={(e) =>
              handleChange('interest_calculation_type', e.target.value as InterestCalculationType)
            }
            disabled={isPending}
          />

          {/* Payout Frequency */}
          <Select
            label="Interest Payout Frequency"
            options={PAYOUT_FREQUENCY_OPTIONS}
            value={formData.interest_payout_frequency}
            onChange={(e) =>
              handleChange('interest_payout_frequency', e.target.value as InterestPayoutFrequency)
            }
            disabled={isPending}
          />

          {/* Auto-renewal Checkbox */}
          <div className={styles.checkboxField}>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={formData.auto_renewal}
                onChange={(e) => handleChange('auto_renewal', e.target.checked)}
                disabled={isPending}
                className={styles.checkbox}
              />
              <span>Auto-renewal enabled</span>
            </label>
          </div>

          {/* Notes */}
          <div className={styles.fullWidth}>
            <Textarea
              label="Notes"
              placeholder="Optional notes about this fixed deposit"
              value={formData.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              error={errors.notes}
              disabled={isPending}
              rows={3}
            />
          </div>
        </div>

        <ModalFooter>
          <Button variant="ghost" onClick={onClose} disabled={isPending} type="button">
            Cancel
          </Button>
          <Button type="submit" loading={isPending}>
            {isEditMode ? 'Save Changes' : 'Create Fixed Deposit'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  );
}

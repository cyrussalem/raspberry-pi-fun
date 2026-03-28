import { TestBed } from '@angular/core/testing';
import { MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';
import { KeypadDialogComponent } from './keypad-dialog.component';
import { AccessService } from '../../services/access.service';
import { HttpErrorResponse } from '@angular/common/http';

describe('KeypadDialogComponent', () => {
  let component: KeypadDialogComponent;
  let accessServiceSpy: jest.SpyObj<AccessService>;
  let dialogRefSpy: jest.SpyObj<MatDialogRef<KeypadDialogComponent>>;
  let snackBarSpy: jest.SpyObj<MatSnackBar>;

  beforeEach(async () => {
    accessServiceSpy = { verifyCode: jest.fn(), updateCode: jest.fn() } as any;
    dialogRefSpy = { close: jest.fn() } as any;
    snackBarSpy = { open: jest.fn() } as any;

    await TestBed.configureTestingModule({
      imports: [KeypadDialogComponent],
    })
      .overrideComponent(KeypadDialogComponent, {
        set: {
          providers: [
            { provide: AccessService, useValue: accessServiceSpy },
            { provide: MatDialogRef, useValue: dialogRefSpy },
            { provide: MatSnackBar, useValue: snackBarSpy },
          ],
        },
      })
      .compileComponents();

    const fixture = TestBed.createComponent(KeypadDialogComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start with empty code', () => {
    expect(component.enteredCode).toBe('');
  });

  it('should append digits on key press', () => {
    component.onKeyPress('1');
    component.onKeyPress('2');
    component.onKeyPress('3');
    expect(component.enteredCode).toBe('123');
  });

  it('should remove last digit on backspace', () => {
    component.enteredCode = '1234';
    component.onKeyPress('backspace');
    expect(component.enteredCode).toBe('123');
  });

  it('should handle backspace on empty code', () => {
    component.onKeyPress('backspace');
    expect(component.enteredCode).toBe('');
  });

  it('should limit code to 8 digits', () => {
    component.enteredCode = '12345678';
    component.onKeyPress('9');
    expect(component.enteredCode).toBe('12345678');
  });

  it('should mask code as dots', () => {
    component.enteredCode = '1234';
    expect(component.maskedCode).toBe('\u25CF\u25CF\u25CF\u25CF');
  });

  it('should return empty string for empty code mask', () => {
    expect(component.maskedCode).toBe('');
  });

  it('should not process keys while submitting', () => {
    component.isSubmitting = true;
    component.onKeyPress('1');
    expect(component.enteredCode).toBe('');
  });

  it('should call verifyCode on submit', () => {
    accessServiceSpy.verifyCode.mockReturnValue(
      of({ status: 'success' as const, message: 'Access granted.' })
    );
    component.enteredCode = '1234';
    component.submit();
    expect(accessServiceSpy.verifyCode).toHaveBeenCalledWith('1234');
  });

  it('should close dialog on successful verify', () => {
    accessServiceSpy.verifyCode.mockReturnValue(
      of({ status: 'success' as const, message: 'Access granted.' })
    );
    component.enteredCode = '1234';
    component.submit();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(true);
    expect(snackBarSpy.open).toHaveBeenCalled();
  });

  it('should clear code and show error on failed verify', () => {
    const errorResponse = new HttpErrorResponse({
      error: { status: 'error', message: 'Access denied.' },
      status: 403,
    });
    accessServiceSpy.verifyCode.mockReturnValue(throwError(() => errorResponse));
    component.enteredCode = '9999';
    component.submit();
    expect(component.enteredCode).toBe('');
    expect(component.isSubmitting).toBe(false);
    expect(snackBarSpy.open).toHaveBeenCalled();
  });

  it('should not submit with empty code', () => {
    component.submit();
    expect(accessServiceSpy.verifyCode).not.toHaveBeenCalled();
  });

  it('should not submit while already submitting', () => {
    component.enteredCode = '1234';
    component.isSubmitting = true;
    component.submit();
    expect(accessServiceSpy.verifyCode).not.toHaveBeenCalled();
  });

  it('should trigger submit on check key press', () => {
    accessServiceSpy.verifyCode.mockReturnValue(
      of({ status: 'success' as const, message: 'Access granted.' })
    );
    component.enteredCode = '1234';
    component.onKeyPress('check');
    expect(accessServiceSpy.verifyCode).toHaveBeenCalledWith('1234');
  });
});

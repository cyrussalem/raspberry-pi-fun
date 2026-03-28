import { TestBed } from '@angular/core/testing';
import { MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';
import { UpdateCodeDialogComponent } from './update-code-dialog.component';
import { AccessService } from '../../services/access.service';
import { HttpErrorResponse } from '@angular/common/http';

describe('UpdateCodeDialogComponent', () => {
  let component: UpdateCodeDialogComponent;
  let accessServiceSpy: jest.SpyObj<AccessService>;
  let dialogRefSpy: jest.SpyObj<MatDialogRef<UpdateCodeDialogComponent>>;
  let snackBarSpy: jest.SpyObj<MatSnackBar>;

  beforeEach(async () => {
    accessServiceSpy = { verifyCode: jest.fn(), updateCode: jest.fn() } as any;
    dialogRefSpy = { close: jest.fn() } as any;
    snackBarSpy = { open: jest.fn() } as any;

    await TestBed.configureTestingModule({
      imports: [UpdateCodeDialogComponent],
    })
      .overrideComponent(UpdateCodeDialogComponent, {
        set: {
          providers: [
            { provide: AccessService, useValue: accessServiceSpy },
            { provide: MatDialogRef, useValue: dialogRefSpy },
            { provide: MatSnackBar, useValue: snackBarSpy },
          ],
        },
      })
      .compileComponents();

    const fixture = TestBed.createComponent(UpdateCodeDialogComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start with empty fields', () => {
    expect(component.currentCode).toBe('');
    expect(component.newCode).toBe('');
    expect(component.error).toBeNull();
  });

  describe('isValid', () => {
    it('should be invalid when both fields are empty', () => {
      expect(component.isValid).toBe(false);
    });

    it('should be invalid when current code is too short', () => {
      component.currentCode = '12';
      component.newCode = '5678';
      expect(component.isValid).toBe(false);
    });

    it('should be invalid when new code is too short', () => {
      component.currentCode = '1234';
      component.newCode = '12';
      expect(component.isValid).toBe(false);
    });

    it('should be invalid when new code is non-numeric', () => {
      component.currentCode = '1234';
      component.newCode = 'abcd';
      expect(component.isValid).toBe(false);
    });

    it('should be valid when both codes are 4+ digits', () => {
      component.currentCode = '0000';
      component.newCode = '1234';
      expect(component.isValid).toBe(true);
    });

    it('should be valid with longer codes', () => {
      component.currentCode = '123456';
      component.newCode = '654321';
      expect(component.isValid).toBe(true);
    });
  });

  describe('submit', () => {
    it('should call updateCode on submit', () => {
      accessServiceSpy.updateCode.mockReturnValue(
        of({ status: 'success' as const, message: 'Updated.' })
      );
      component.currentCode = '0000';
      component.newCode = '1234';
      component.submit();
      expect(accessServiceSpy.updateCode).toHaveBeenCalledWith('0000', '1234');
    });

    it('should close dialog on success', () => {
      accessServiceSpy.updateCode.mockReturnValue(
        of({ status: 'success' as const, message: 'Updated.' })
      );
      component.currentCode = '0000';
      component.newCode = '1234';
      component.submit();
      expect(dialogRefSpy.close).toHaveBeenCalledWith(true);
      expect(snackBarSpy.open).toHaveBeenCalled();
    });

    it('should show error on failed update', () => {
      const errorResponse = new HttpErrorResponse({
        error: { status: 'error', message: 'Current access code is incorrect.' },
        status: 403,
      });
      accessServiceSpy.updateCode.mockReturnValue(throwError(() => errorResponse));
      component.currentCode = '9999';
      component.newCode = '1234';
      component.submit();
      expect(component.error).toBe('Current access code is incorrect.');
      expect(component.isSubmitting).toBe(false);
      expect(dialogRefSpy.close).not.toHaveBeenCalled();
    });

    it('should not submit when invalid', () => {
      component.currentCode = '';
      component.newCode = '';
      component.submit();
      expect(accessServiceSpy.updateCode).not.toHaveBeenCalled();
    });

    it('should not submit while already submitting', () => {
      component.currentCode = '0000';
      component.newCode = '1234';
      component.isSubmitting = true;
      component.submit();
      expect(accessServiceSpy.updateCode).not.toHaveBeenCalled();
    });

    it('should clear error before submitting', () => {
      accessServiceSpy.updateCode.mockReturnValue(
        of({ status: 'success' as const, message: 'Updated.' })
      );
      component.error = 'Previous error';
      component.currentCode = '0000';
      component.newCode = '1234';
      component.submit();
      expect(component.error).toBeNull();
    });
  });
});

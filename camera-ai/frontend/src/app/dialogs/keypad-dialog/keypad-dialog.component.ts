import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AccessService } from '../../services/access.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-keypad-dialog',
  standalone: true,
  imports: [MatDialogModule, MatButtonModule, MatIconModule, MatSnackBarModule],
  templateUrl: './keypad-dialog.component.html',
  styleUrl: './keypad-dialog.component.css',
})
export class KeypadDialogComponent {
  enteredCode = '';
  isSubmitting = false;

  readonly keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'backspace', '0', 'check'];

  constructor(
    private dialogRef: MatDialogRef<KeypadDialogComponent>,
    private accessService: AccessService,
    private snackBar: MatSnackBar
  ) {}

  onKeyPress(key: string): void {
    if (this.isSubmitting) return;

    if (key === 'backspace') {
      this.enteredCode = this.enteredCode.slice(0, -1);
    } else if (key === 'check') {
      this.submit();
    } else if (this.enteredCode.length < 8) {
      this.enteredCode += key;
    }
  }

  submit(): void {
    if (!this.enteredCode || this.isSubmitting) return;

    this.isSubmitting = true;
    this.accessService.verifyCode(this.enteredCode).subscribe({
      next: (response) => {
        this.snackBar.open(response.message, 'OK', {
          duration: 4000,
          panelClass: ['snackbar-success'],
        });
        this.dialogRef.close(true);
      },
      error: (err: HttpErrorResponse) => {
        const message = err.error?.message || 'An error occurred.';
        this.snackBar.open(message, 'OK', {
          duration: 4000,
          panelClass: ['snackbar-error'],
        });
        this.enteredCode = '';
        this.isSubmitting = false;
      },
    });
  }

  get maskedCode(): string {
    return '\u25CF'.repeat(this.enteredCode.length);
  }
}

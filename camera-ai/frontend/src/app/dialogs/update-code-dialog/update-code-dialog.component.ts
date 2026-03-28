import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AccessService } from '../../services/access.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-update-code-dialog',
  standalone: true,
  imports: [
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSnackBarModule,
  ],
  templateUrl: './update-code-dialog.component.html',
  styleUrl: './update-code-dialog.component.css',
})
export class UpdateCodeDialogComponent {
  currentCode = '';
  newCode = '';
  error: string | null = null;
  isSubmitting = false;

  constructor(
    private dialogRef: MatDialogRef<UpdateCodeDialogComponent>,
    private accessService: AccessService,
    private snackBar: MatSnackBar
  ) {}

  get isValid(): boolean {
    return (
      this.currentCode.length >= 4 &&
      this.newCode.length >= 4 &&
      /^\d+$/.test(this.newCode)
    );
  }

  submit(): void {
    if (!this.isValid || this.isSubmitting) return;

    this.error = null;
    this.isSubmitting = true;

    this.accessService.updateCode(this.currentCode, this.newCode).subscribe({
      next: (response) => {
        this.snackBar.open(response.message, 'OK', {
          duration: 4000,
          panelClass: ['snackbar-success'],
        });
        this.dialogRef.close(true);
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.message || 'An error occurred.';
        this.isSubmitting = false;
      },
    });
  }
}
